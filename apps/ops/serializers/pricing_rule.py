from decimal import Decimal

from psycopg2.extras import DateTimeTZRange
from rest_framework import serializers

from apps.ops.models import PricingRule


class PricingRuleSerializer(serializers.ModelSerializer):
    start_period = serializers.DateTimeField(source="valid_period.lower")
    end_period = serializers.DateTimeField(source="valid_period.upper")

    class Meta:
        model = PricingRule
        fields = [
            "id", "name", "scope", "rule_type", "priority",
            "start_period", "end_period",
            "multiplier", "flat_fee", "is_active",
            "price_per_day", "free_km_per_day", "price_per_extra_km",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "priority": {"min_value": 0},
            "multiplier": {"min_value": Decimal("0.01")},
            "flat_fee": {"min_value": Decimal("0")},
            "price_per_day": {"min_value": Decimal("0")},
            "free_km_per_day": {"min_value": 0},
            "price_per_extra_km": {"min_value": Decimal("0")},
        }

    def validate(self, attrs):
        period = attrs.pop("valid_period", None)
        if period is None:
            return attrs


        current = getattr(self.instance, "valid_period", None)
        lower = period.get("lower", current.lower if current else None)
        upper = period.get("upper", current.upper if current else None)

        if lower is None or upper is None:
            raise serializers.ValidationError(
                "start_period va end_period ikkalasi ham kerak."
            )
        if lower >= upper:
            raise serializers.ValidationError(
                {"end_period": "start_period'dan keyin bo'lishi kerak"}
            )

        attrs["valid_period"] = DateTimeTZRange(lower, upper)
        return attrs