from django.db import transaction, IntegrityError
from psycopg2.extras import DateTimeTZRange

from apps.accounts.models import Customer
from apps.booking.models import Booking
from apps.booking.enums import BookingStatus
from apps.booking.services.payment import PaymentService
from apps.fleet.models import Car
from apps.booking.exceptions import (
    CarNotAvailableForPeriodError,
    BookingNotFoundError,
    BookingNotCancellableError,
)
from root.exceptions import PermissionDeniedError


class BookingService:
    def create_booking(
        self, *,
        customer,
        car_id: int,
        pickup_station_id: int,
        dropoff_station_id: int,
        period: DateTimeTZRange,
        total_price,
        idempotency_key,
    ) -> tuple[Booking, bool]:
        """
        Creates new booking checks the idempotency_key

        Returns:
            (booking, is_replay): is_replay=True when the key was already used.
        """
        existing = Booking.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, True

        try:
            with transaction.atomic():
                car = Car.objects.select_for_update().get(id=car_id)

                booking = Booking.objects.create(
                    customer=customer,
                    car=car,
                    pickup_station_id=pickup_station_id,
                    dropoff_station_id=dropoff_station_id,
                    period=period,
                    status=BookingStatus.PENDING,
                    total_price=total_price,
                    idempotency_key=idempotency_key,
                )

                PaymentService().create_hold(booking=booking, amount=total_price)

                booking.status = BookingStatus.CONFIRMED
                booking.save(update_fields=["status", "updated_at"])

                return booking, False

        except IntegrityError as e:
            if 'exclude_overlapping_bookings' in str(e):
                raise CarNotAvailableForPeriodError(car_id=car_id, period=str(period))
            if 'idempotency_key' in str(e):
                existing = Booking.objects.get(idempotency_key=idempotency_key)
                return existing, True
            raise


    def create_booking_from_user(
        self, *,
        user,
        car_id: int,
        pickup_station_id: int,
        dropoff_station_id: int,
        period: DateTimeTZRange,
        total_price,
        idempotency_key,
        **_,
    ) -> tuple[Booking, bool]:
        try:
            customer = Customer.objects.get(user_id=user.pk)
        except Customer.DoesNotExist:
            raise PermissionDeniedError()
        return self.create_booking(
            customer=customer,
            car_id=car_id,
            pickup_station_id=pickup_station_id,
            dropoff_station_id=dropoff_station_id,
            period=period,
            total_price=total_price,
            idempotency_key=idempotency_key,
        )

    def cancel_booking(self, *, booking_id: int, customer) -> Booking:
        with transaction.atomic():
            try:
                booking = Booking.objects.select_for_update().get(id=booking_id)
            except Booking.DoesNotExist:
                raise BookingNotFoundError(booking_id=booking_id)

            if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
                raise BookingNotCancellableError(
                    booking_id=booking_id, current_status=booking.status
                )

            booking.status = BookingStatus.CANCELLED
            booking.save(update_fields=["status", "updated_at"])

            PaymentService().cancel_hold(booking=booking)

            return booking