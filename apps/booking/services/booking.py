from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import QuerySet
import math
from psycopg2.extras import DateTimeTZRange

from apps.accounts.models import Customer
from apps.booking.enums import BookingStatus
from apps.booking.exceptions import (
    BookingNotCancellableError,
    BookingNotFoundError,
    CarNotAvailableForPeriodError,
)
from apps.booking.models import Booking
from apps.booking.services.outbox import emit
from apps.booking.services.payment import PaymentService
from apps.fleet.exceptions import CarNotFoundError
from apps.fleet.models import Car
from apps.ops.models import PricingRule
from apps.rental.exceptions import PricingRuleNotFoundError
from root.exceptions import PermissionDeniedError


class BookingService:
    def create_booking(
        self,
        *,
        customer,
        car_id: int,
        pickup_station_id: int,
        dropoff_station_id: int,
        period: DateTimeTZRange,
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
                try:
                    car = Car.objects.select_for_update().get(id=car_id)
                except Car.DoesNotExist:
                    raise CarNotFoundError(car_id=car_id)

                pricing_rule = (
                    PricingRule.objects.filter(is_active=True, valid_period__overlap=period)
                    .order_by("-priority")
                    .first()
                )
                if pricing_rule is None:
                    raise PricingRuleNotFoundError(car_model_id=car.carModel_id)

                hold_amount = self._calculate_hold_amount(rule=pricing_rule, period=period)

                booking = Booking.objects.create(
                    customer=customer,
                    car=car,
                    pricing_rule=pricing_rule,
                    pickup_station_id=pickup_station_id,
                    dropoff_station_id=dropoff_station_id,
                    period=period,
                    status=BookingStatus.PENDING,
                    total_price=hold_amount,
                    idempotency_key=idempotency_key,
                )

                PaymentService().create_hold(booking=booking, amount=hold_amount)

                booking.status = BookingStatus.CONFIRMED
                booking.save(update_fields=["status", "updated_at"])

                emit(
                    aggregate_type="booking",
                    aggregate_id=booking.id,
                    event_type="booking.created",
                    payload={
                        "booking_id": booking.id,
                        "customer_id": booking.customer_id,
                        "car_id": booking.car_id,
                        "status": booking.status,
                        "total_price": str(booking.total_price),
                    },
                )
                return booking, False

        except IntegrityError as e:
            if "exclude_overlapping_bookings" in str(e):
                raise CarNotAvailableForPeriodError(car_id=car_id, period=str(period))
            if "idempotency_key" in str(e):
                return Booking.objects.get(idempotency_key=idempotency_key), True
            raise

    def _calculate_hold_amount(self, *, rule: PricingRule, period: DateTimeTZRange) -> Decimal:
        seconds = (period.upper - period.lower).total_seconds()
        days = max(1, math.ceil(seconds / 86400))  # yuqoriga yaxlitlanadi
        return rule.price_per_day * days * rule.multiplier + rule.flat_fee

    def create_booking_from_user(
        self,
        *,
        user,
        car_id: int,
        pickup_station_id: int,
        dropoff_station_id: int,
        period: DateTimeTZRange,
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
            #total_price=total_price,
            idempotency_key=idempotency_key,
        )

    def list_bookings(
        self,
        *,
        customer_id: int | None = None,
        status: str | None = None,
        car_id: int | None = None,
    ) -> QuerySet:
        qs = Booking.objects.select_related(
            "customer", "car", "pickup_station", "dropoff_station"
        )
        if customer_id is not None:
            qs = qs.filter(customer_id=customer_id)
        if status is not None:
            qs = qs.filter(status=status)
        if car_id is not None:
            qs = qs.filter(car_id=car_id)
        return qs

    def get_booking(self, *, booking_id: int) -> Booking:
        try:
            return Booking.objects.select_related(
                "customer", "car", "pickup_station", "dropoff_station"
            ).get(id=booking_id)
        except Booking.DoesNotExist:
            raise BookingNotFoundError(booking_id=booking_id)

    def update_booking(self, *, booking_id: int, **data) -> Booking:
        booking = self.get_booking(booking_id=booking_id)
        update_fields = []
        for field, value in data.items():
            setattr(booking, field, value)
            update_fields.append(field)
        if update_fields:
            update_fields.append("updated_at")
            booking.save(update_fields=update_fields)
        return booking

    def delete_booking(self, *, booking_id: int) -> None:
        booking = self.get_booking(booking_id=booking_id)
        booking.delete()
        emit(
            aggregate_type="booking",
            aggregate_id=booking_id,
            event_type="booking.deleted",
            payload={"booking_id": booking_id},
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

            emit(
                aggregate_type="booking",
                aggregate_id=booking_id,
                event_type="booking.cancelled",
                payload={"booking_id": booking_id, "customer_id": booking.customer_id},
            )
            return booking
