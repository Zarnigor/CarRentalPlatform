import pytest
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal

from apps.damage.enums import DamageSeverity, DamageType
from apps.rental.enums import RentalStatus
from apps.rental.models import Rental
from apps.damage.models import Damage


def _utc(hours: int = 0) -> datetime:
    return datetime(2025, 6, 1, tzinfo=timezone.utc) + timedelta(hours=hours)


@pytest.fixture
def rental(confirmed_booking):
    return Rental.objects.create(
        booking=confirmed_booking,
        started_at=_utc(0),
        ended_at=_utc(4),
        start_odometer=Decimal("10000.00"),
        end_odometer=Decimal("10100.00"),
        status=RentalStatus.DISPUTED,
    )


@pytest.mark.django_db
class TestDamageModel:

    def test_creates_damage(self, rental):
        damage = Damage.objects.create(
            rental=rental,
            damage_type=DamageType.SCRATCH,
            severity=DamageSeverity.MINOR,
            location="front_bumper",
            description="Small surface scratch",
            estimated_cost=Decimal("50000.00"),
            reported_at=date(2025, 6, 1),
        )
        assert damage.pk is not None

    def test_all_damage_types_valid(self, rental):
        for i, dtype in enumerate(DamageType.values):
            d = Damage.objects.create(
                rental=rental,
                damage_type=dtype,
                severity=DamageSeverity.MINOR,
                location=f"loc_{i}",
                description="test",
                estimated_cost=Decimal("10000.00"),
                reported_at=date(2025, 6, 1),
            )
            assert d.damage_type == dtype

    def test_all_severities_valid(self, rental):
        for i, sev in enumerate(DamageSeverity.values):
            d = Damage.objects.create(
                rental=rental,
                damage_type=DamageType.DENT,
                severity=sev,
                location=f"loc_{i}",
                description="test",
                estimated_cost=Decimal("10000.00"),
                reported_at=date(2025, 6, 1),
            )
            assert d.severity == sev

    def test_resolved_at_auto_populated(self, rental):
        damage = Damage.objects.create(
            rental=rental,
            damage_type=DamageType.CRACK,
            severity=DamageSeverity.MODERATE,
            location="windshield",
            description="Crack",
            estimated_cost=Decimal("500000.00"),
            reported_at=date(2025, 6, 1),
        )
        assert damage.resolved_at is not None

    def test_cascade_delete_with_rental(self, rental):
        Damage.objects.create(
            rental=rental,
            damage_type=DamageType.SCRATCH,
            severity=DamageSeverity.MINOR,
            location="hood",
            description="Scratch",
            estimated_cost=Decimal("30000.00"),
            reported_at=date(2025, 6, 1),
        )
        rental_pk = rental.pk
        rental.delete()
        assert Damage.objects.filter(rental_id=rental_pk).count() == 0
