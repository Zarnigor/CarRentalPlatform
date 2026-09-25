from rest_framework import serializers

from apps.rental.enums import RentalStatus
from apps.rental.models import Rental


class RentalStartSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    start_odometer = serializers.DecimalField(max_digits=10, decimal_places=2)


class RentalUpdateSerializer(serializers.Serializer):
    start_odometer = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    end_odometer = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    status = serializers.ChoiceField(choices=RentalStatus.choices, required=False)
    started_at = serializers.DateTimeField(required=False)
    ended_at = serializers.DateTimeField(required=False)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    extra_km_charged = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class DamageInputSerializer(serializers.Serializer):
    damage_type = serializers.CharField(max_length=20)
    severity = serializers.CharField(max_length=20)
    location = serializers.CharField(max_length=20)
    description = serializers.CharField()
    estimated_cost = serializers.DecimalField(max_digits=10, decimal_places=2)


class RentalFinishSerializer(serializers.Serializer):
    end_odometer = serializers.DecimalField(max_digits=10, decimal_places=2)
    dropoff_lat = serializers.FloatField()
    dropoff_lon = serializers.FloatField()
    damages = DamageInputSerializer(many=True, required=False, default=list)


class RentalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = [
            "id", "booking", "started_at", "ended_at",
            "start_odometer", "end_odometer", "status",
            "final_price", "extra_km_charged",
        ]
        read_only_fields = fields
