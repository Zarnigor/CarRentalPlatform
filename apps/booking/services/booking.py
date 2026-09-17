from django.db import transaction, IntegrityError
from psycopg2.extras import DateTimeTZRange

from apps.booking.models import Booking
from apps.booking.enums import BookingStatus
from apps.booking.services.payment import PaymentService
from apps.fleet.models import Car
from apps.booking.exceptions import (
    CarNotAvailableForPeriodError,
    BookingNotFoundError,
    BookingNotCancellableError
)


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
    ) -> Booking:
        """
        Yangi booking yaratadi. idempotency_key orqali takroriy so'rovlar himoyalanadi.
        """
        existing = Booking.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing

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

                return booking

        except IntegrityError as e:
            if 'exclude_overlapping_bookings' in str(e):
                raise CarNotAvailableForPeriodError(car_id=car_id, period=str(period))
            if 'idempotency_key' in str(e):
                existing = Booking.objects.get(idempotency_key=idempotency_key)
                return existing
            raise


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