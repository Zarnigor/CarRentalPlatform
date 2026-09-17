import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from psycopg2.extras import DateTimeTZRange

from apps.booking.enums import PricingRuleType, PricingScope
from apps.booking.models import PricingRule


def _utc(hours: int = 0) -> datetime:
    return datetime(2025, 6, 1, tzinfo=timezone.utc) + timedelta(hours=hours)


@pytest.mark.django_db
class TestPricingRuleModel:

    def test_creates_pricing_rule(self, pricing_rule):
        assert pricing_rule.pk is not None

    def test_is_active_defaults_to_true(self):
        rule = PricingRule.objects.create(
            name="Test Rule",
            scope=PricingScope.GLOBAL,
            rule_type=PricingRuleType.SEASONAL,
            valid_period=DateTimeTZRange(_utc(0), _utc(100)),
            flat_fee=Decimal("0.00"),
            price_per_day=Decimal("100000.00"),
            price_per_extra_km=Decimal("500.00"),
        )
        assert rule.is_active is True

    def test_priority_defaults_to_zero(self):
        rule = PricingRule.objects.create(
            name="Priority Test",
            scope=PricingScope.GLOBAL,
            rule_type=PricingRuleType.WEEKEND,
            valid_period=DateTimeTZRange(_utc(0), _utc(100)),
            flat_fee=Decimal("0.00"),
            price_per_day=Decimal("100000.00"),
            price_per_extra_km=Decimal("500.00"),
        )
        assert rule.priority == 0

    def test_multiplier_defaults_to_one(self):
        rule = PricingRule.objects.create(
            name="Multiplier Test",
            scope=PricingScope.GLOBAL,
            rule_type=PricingRuleType.SEASONAL,
            valid_period=DateTimeTZRange(_utc(0), _utc(100)),
            flat_fee=Decimal("0.00"),
            price_per_day=Decimal("100000.00"),
            price_per_extra_km=Decimal("500.00"),
        )
        assert rule.multiplier == 1

    def test_free_km_per_day_defaults_to_zero(self):
        rule = PricingRule.objects.create(
            name="Free KM Test",
            scope=PricingScope.GLOBAL,
            rule_type=PricingRuleType.SEASONAL,
            valid_period=DateTimeTZRange(_utc(0), _utc(100)),
            flat_fee=Decimal("0.00"),
            price_per_day=Decimal("100000.00"),
            price_per_extra_km=Decimal("500.00"),
        )
        assert rule.free_km_per_day == 0

    def test_valid_period_is_range(self, pricing_rule):
        pricing_rule.refresh_from_db()
        assert hasattr(pricing_rule.valid_period, "lower")
        assert hasattr(pricing_rule.valid_period, "upper")
