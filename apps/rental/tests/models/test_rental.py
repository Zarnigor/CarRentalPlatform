import pytest
from decimal import Decimal

from apps.rental.enums import RentalStatus
from apps.rental.models import Rental


@pytest.mark.django_db
class TestRentalModel:

    # ── field defaults ────────────────────────────────────────────────────────

    def test_status_defaults_to_active(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.status == RentalStatus.ACTIVE

    def test_extra_km_charged_defaults_to_zero(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.extra_km_charged == Decimal("0")

    # ── nullable fields ───────────────────────────────────────────────────────

    def test_started_at_is_nullable(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.started_at is None

    def test_ended_at_is_nullable(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.ended_at is None

    def test_final_price_is_nullable(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert rental.final_price is None

    # ── persistence ───────────────────────────────────────────────────────────

    def test_creates_and_gets_pk(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"),
            end_odometer=Decimal("10000.00"),
        )
        assert rental.pk is not None
        assert Rental.objects.filter(pk=rental.pk).exists()

    def test_all_status_choices_are_storable(self, confirmed_booking):
        for status in RentalStatus.values:
            rental = Rental.objects.create(
                booking=confirmed_booking,
                start_odometer=Decimal("0"),
                end_odometer=Decimal("0"),
                status=status,
            )
            rental.refresh_from_db()
            assert rental.status == status

    def test_final_price_and_extra_km_can_be_set(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"),
            end_odometer=Decimal("10200.00"),
            final_price=Decimal("210000.00"),
            extra_km_charged=Decimal("50000.00"),
        )
        rental.refresh_from_db()
        assert rental.final_price == Decimal("210000.00")
        assert rental.extra_km_charged == Decimal("50000.00")

    def test_odometer_precision(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.12"),
            end_odometer=Decimal("10250.75"),
        )
        rental.refresh_from_db()
        assert rental.start_odometer == Decimal("10000.12")
        assert rental.end_odometer == Decimal("10250.75")

    # ── relations ─────────────────────────────────────────────────────────────

    def test_reverse_relation_from_booking(self, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        assert confirmed_booking.rentals.count() == 1

    def test_multiple_rentals_per_booking_are_allowed(self, confirmed_booking):
        for _ in range(3):
            Rental.objects.create(
                booking=confirmed_booking,
                start_odometer=Decimal("0"),
                end_odometer=Decimal("0"),
            )
        assert confirmed_booking.rentals.count() == 3

    def test_cascade_delete_with_booking(self, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"),
            end_odometer=Decimal("0"),
        )
        pk = confirmed_booking.pk
        confirmed_booking.delete()
        assert Rental.objects.filter(booking_id=pk).count() == 0
