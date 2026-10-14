import pytest
from datetime import date
from decimal import Decimal

from apps.damage.serializers import DamageWriteSerializer


@pytest.mark.django_db
class TestDamageWriteSerializerValidateEstimatedCost:

    def test_rejects_negative_estimated_cost(self, active_rental):
        s = DamageWriteSerializer(data={
            "rental": active_rental.pk,
            "damage_type": "SCRATCH",
            "severity": "MINOR",
            "location": "front",
            "description": "test",
            "estimated_cost": "-1.00",
            "reported_at": date.today().isoformat(),
        })
        assert not s.is_valid()
        assert "estimated_cost" in s.errors

    def test_accepts_zero_estimated_cost(self, active_rental):
        s = DamageWriteSerializer(data={
            "rental": active_rental.pk,
            "damage_type": "SCRATCH",
            "severity": "MINOR",
            "location": "front",
            "description": "test",
            "estimated_cost": "0.00",
            "reported_at": date.today().isoformat(),
        })
        assert s.is_valid(), s.errors

    def test_accepts_positive_estimated_cost(self, active_rental):
        s = DamageWriteSerializer(data={
            "rental": active_rental.pk,
            "damage_type": "DENT",
            "severity": "MODERATE",
            "location": "door",
            "description": "dent",
            "estimated_cost": "150000.00",
            "reported_at": date.today().isoformat(),
        })
        assert s.is_valid(), s.errors
