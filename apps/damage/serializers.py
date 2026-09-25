from rest_framework import serializers
from apps.damage.models import Damage
from apps.rental.models import Rental


class DamageReadSerializer(serializers.ModelSerializer):
    damage_type_display = serializers.CharField(source="get_damage_type_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)

    class Meta:
        model = Damage
        fields = [
            "id", "rental", "damage_type", "damage_type_display",
            "severity", "severity_display", "location",
            "description", "estimated_cost", "reported_at", "resolved_at",
        ]


class DamageWriteSerializer(serializers.ModelSerializer):
    rental = serializers.PrimaryKeyRelatedField(queryset=Rental.objects.all())

    class Meta:
        model = Damage
        fields = [
            "rental", "damage_type", "severity",
            "location", "description", "estimated_cost", "reported_at",
        ]

    def validate_estimated_cost(self, value):
        if value < 0:
            raise serializers.ValidationError("Estimated cost manfiy bo'lishi mumkin emas.")
        return value