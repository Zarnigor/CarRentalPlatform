import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from apps.booking.enums import RentalStatus
from apps.booking.models import Rental
from apps.booking.services.ops import OpsService


def _utc(hours_offset: int = 0) -> datetime:
    base = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(hours=hours_offset)


@pytest.mark.django_db
class TestGetUtilization:

    def test_returns_empty_when_no_cars(self):
        service = OpsService()
        result = service.get_utilization(
            date_from=_utc(0),
            date_to=_utc(2),
            granularity="hour",
        )
        assert result == []

    def test_returns_zero_utilization_with_no_rentals(self, car):
        service = OpsService()
        result = service.get_utilization(
            date_from=_utc(0),
            date_to=_utc(2),
            granularity="hour",
        )

        assert len(result) == 2
        for bucket in result:
            assert bucket["utilization_pct"] == Decimal("0.00")

    def test_100_percent_when_car_rented_full_hour(self, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            started_at=_utc(0),
            ended_at=_utc(1),
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
            status=RentalStatus.COMPLETED,
        )

        service = OpsService()
        result = service.get_utilization(
            date_from=_utc(0),
            date_to=_utc(1),
            granularity="hour",
        )

        assert len(result) == 1
        assert result[0]["utilization_pct"] == Decimal("100.00")

    def test_partial_utilization_for_half_hour_rental(self, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            started_at=_utc(0),
            ended_at=_utc(0) + timedelta(minutes=30),
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
            status=RentalStatus.COMPLETED,
        )

        service = OpsService()
        result = service.get_utilization(
            date_from=_utc(0),
            date_to=_utc(1),
            granularity="hour",
        )

        assert result[0]["utilization_pct"] == Decimal("50.00")

    def test_day_granularity_produces_correct_buckets(self, car):
        service = OpsService()
        result = service.get_utilization(
            date_from=_utc(0),
            date_to=_utc(48),
            granularity="day",
        )

        assert len(result) == 2
        for bucket in result:
            assert "period_start" in bucket
            assert "period_end" in bucket
            assert "utilization_pct" in bucket

    def test_active_rental_with_no_end_counts_as_ongoing(self, confirmed_booking):
        """Rentals with ended_at=None should count up to now."""
        Rental.objects.create(
            booking=confirmed_booking,
            started_at=_utc(0),
            ended_at=None,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
            status=RentalStatus.ACTIVE,
        )

        service = OpsService()
        result = service.get_utilization(
            date_from=_utc(0),
            date_to=_utc(1),
            granularity="hour",
        )

        # utilization must be > 0 since rental spans the window
        assert result[0]["utilization_pct"] > Decimal("0")
