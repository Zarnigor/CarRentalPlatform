from datetime import datetime, timedelta, timezone
from decimal import Decimal

from apps.ops.serializers.pricing_rule import PricingRuleSerializer


def _utc(hours=0):
    return datetime(2025, 6, 1, tzinfo=timezone.utc) + timedelta(hours=hours)


def _base(**overrides):
    data = {
        "name": "Standard",
        "scope": "GLOBAL",
        "rule_type": "SEASONAL",
        "priority": 0,
        "start_period": _utc(0).isoformat(),
        "end_period": _utc(100).isoformat(),
        "multiplier": "1.00",
        "flat_fee": "0.00",
        "price_per_day": "150000.00",
        "free_km_per_day": 100,
        "price_per_extra_km": "500.00",
    }
    data.update(overrides)
    return data


class TestPricingRuleSerializerValidate:

    def test_valid_data_passes(self):
        s = PricingRuleSerializer(data=_base())
        assert s.is_valid(), s.errors

    def test_builds_valid_period_range(self):
        s = PricingRuleSerializer(data=_base())
        assert s.is_valid(), s.errors
        assert s.validated_data["valid_period"].lower == _utc(0)
        assert s.validated_data["valid_period"].upper == _utc(100)

    def test_rejects_end_period_equal_to_start(self):
        s = PricingRuleSerializer(data=_base(
            start_period=_utc(0).isoformat(),
            end_period=_utc(0).isoformat(),
        ))
        assert not s.is_valid()
        assert "end_period" in s.errors

    def test_rejects_end_period_before_start(self):
        s = PricingRuleSerializer(data=_base(
            start_period=_utc(10).isoformat(),
            end_period=_utc(5).isoformat(),
        ))
        assert not s.is_valid()
        assert "end_period" in s.errors

    def test_rejects_negative_multiplier(self):
        s = PricingRuleSerializer(data=_base(multiplier="0.00"))
        assert not s.is_valid()
        assert "multiplier" in s.errors

    def test_rejects_negative_flat_fee(self):
        s = PricingRuleSerializer(data=_base(flat_fee="-1.00"))
        assert not s.is_valid()
        assert "flat_fee" in s.errors

    def test_rejects_negative_price_per_day(self):
        s = PricingRuleSerializer(data=_base(price_per_day="-1.00"))
        assert not s.is_valid()
        assert "price_per_day" in s.errors

    def test_rejects_negative_priority(self):
        s = PricingRuleSerializer(data=_base(priority=-1))
        assert not s.is_valid()
        assert "priority" in s.errors
