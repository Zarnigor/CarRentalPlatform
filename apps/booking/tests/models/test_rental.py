import pytest
from decimal import Decimal

from apps.booking.enums import RentalStatus
from apps.booking.models import Rental


@pytest.mark.django_db
class TestRentalModel:

    def test_creates_rental(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"),
            end_odometer=Decimal("10000.00"),
        )
        assert rental.pk is not None

    def test_status_defaults_to_active(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.status == RentalStatus.ACTIVE

    def test_started_at_and_ended_at_are_nullable(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.started_at is None
        assert rental.ended_at is None

    def test_final_price_is_nullable(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.final_price is None

    def test_extra_km_charged_defaults_to_zero(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.extra_km_charged == Decimal("0")

    def test_reverse_relation_from_booking(self, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert confirmed_booking.rentals.count() == 1

    def test_cascade_delete_with_booking(self, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        pk = confirmed_booking.pk
        confirmed_booking.delete()
        assert Rental.objects.filter(booking_id=pk).count() == 0
