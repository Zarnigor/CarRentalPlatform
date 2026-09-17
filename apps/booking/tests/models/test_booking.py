import uuid
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.db import IntegrityError

from psycopg2.extras import DateTimeTZRange

from apps.booking.enums import BookingStatus
from apps.booking.models import Booking


def _utc(hours: int = 0) -> datetime:
    return datetime(2025, 6, 1, tzinfo=timezone.utc) + timedelta(hours=hours)


def _period(start_h: int, end_h: int) -> DateTimeTZRange:
    return DateTimeTZRange(_utc(start_h), _utc(end_h))


@pytest.mark.django_db
class TestBookingModel:

    def test_creates_booking(self, confirmed_booking):
        assert confirmed_booking.pk is not None

    def test_status_defaults_to_pending(self, customer, car, station):
        booking = Booking.objects.create(
            customer=customer,
            car=car,
            pickup_station=station,
            dropoff_station=station,
            period=_period(10, 14),
            total_price=Decimal("400000.00"),
        )
        assert booking.status == BookingStatus.PENDING

    def test_idempotency_key_auto_generated(self, customer, car, station):
        booking = Booking.objects.create(
            customer=customer,
            car=car,
            pickup_station=station,
            dropoff_station=station,
            period=_period(20, 24),
            total_price=Decimal("400000.00"),
        )
        assert booking.idempotency_key is not None
        assert isinstance(booking.idempotency_key, uuid.UUID)

    def test_idempotency_key_is_unique(self, customer, car, station):
        key = uuid.uuid4()
        Booking.objects.create(
            customer=customer,
            car=car,
            pickup_station=station,
            dropoff_station=station,
            period=_period(30, 34),
            total_price=Decimal("400000.00"),
            idempotency_key=key,
        )
        with pytest.raises(IntegrityError):
            Booking.objects.create(
                customer=customer,
                car=car,
                pickup_station=station,
                dropoff_station=station,
                period=_period(40, 44),
                total_price=Decimal("400000.00"),
                idempotency_key=key,
            )

    def test_pricing_rule_is_optional(self, customer, car, station):
        booking = Booking.objects.create(
            customer=customer,
            car=car,
            pickup_station=station,
            dropoff_station=station,
            period=_period(50, 54),
            total_price=Decimal("400000.00"),
        )
        assert booking.pricing_rule is None

    def test_created_at_auto_populated(self, confirmed_booking):
        assert confirmed_booking.created_at is not None

    def test_updated_at_changes_on_save(self, confirmed_booking):
        before = confirmed_booking.updated_at
        confirmed_booking.status = BookingStatus.CANCELLED
        confirmed_booking.save(update_fields=["status", "updated_at"])
        confirmed_booking.refresh_from_db()
        assert confirmed_booking.updated_at >= before

    def test_period_is_range_field(self, confirmed_booking):
        confirmed_booking.refresh_from_db()
        assert hasattr(confirmed_booking.period, "lower")
        assert hasattr(confirmed_booking.period, "upper")

    def test_exclusion_constraint_blocks_overlapping_confirmed(self, customer, car, station):
        Booking.objects.create(
            customer=customer, car=car,
            pickup_station=station, dropoff_station=station,
            period=_period(100, 106),
            status=BookingStatus.CONFIRMED,
            total_price=Decimal("600000.00"),
        )
        with pytest.raises(IntegrityError):
            Booking.objects.create(
                customer=customer, car=car,
                pickup_station=station, dropoff_station=station,
                period=_period(104, 110),
                status=BookingStatus.CONFIRMED,
                total_price=Decimal("600000.00"),
            )

    def test_exclusion_constraint_blocks_overlapping_pending(self, customer, car, station):
        Booking.objects.create(
            customer=customer, car=car,
            pickup_station=station, dropoff_station=station,
            period=_period(200, 206),
            status=BookingStatus.PENDING,
            total_price=Decimal("600000.00"),
        )
        with pytest.raises(IntegrityError):
            Booking.objects.create(
                customer=customer, car=car,
                pickup_station=station, dropoff_station=station,
                period=_period(203, 210),
                status=BookingStatus.PENDING,
                total_price=Decimal("600000.00"),
            )

    def test_exclusion_constraint_allows_non_overlapping(self, customer, car, station):
        Booking.objects.create(
            customer=customer, car=car,
            pickup_station=station, dropoff_station=station,
            period=_period(300, 304),
            status=BookingStatus.CONFIRMED,
            total_price=Decimal("400000.00"),
        )
        b2 = Booking.objects.create(
            customer=customer, car=car,
            pickup_station=station, dropoff_station=station,
            period=_period(304, 308),
            status=BookingStatus.CONFIRMED,
            total_price=Decimal("400000.00"),
        )
        assert b2.pk is not None

    def test_exclusion_constraint_ignores_cancelled_bookings(self, customer, car, station):
        Booking.objects.create(
            customer=customer, car=car,
            pickup_station=station, dropoff_station=station,
            period=_period(400, 406),
            status=BookingStatus.CANCELLED,
            total_price=Decimal("400000.00"),
        )
        b2 = Booking.objects.create(
            customer=customer, car=car,
            pickup_station=station, dropoff_station=station,
            period=_period(403, 409),
            status=BookingStatus.CONFIRMED,
            total_price=Decimal("400000.00"),
        )
        assert b2.pk is not None
