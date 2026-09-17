from rest_framework import serializers
from .models import Booking


class BookingCreateSerializer(serializers.Serializer):
    car_id = serializers.IntegerField()
    pickup_station_id = serializers.IntegerField()
    dropoff_station_id = serializers.IntegerField()
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        if data["period_start"] >= data["period_end"]:
            raise serializers.ValidationError(
                {"period_end": "period_end must be after period_start"}
            )
        return data


class BookingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "car", "customer", "pickup_station", "dropoff_station",
            "period", "status", "total_price", "idempotency_key",
            "hold_id", "created_at", "updated_at",
        ]
        read_only_fields = fields