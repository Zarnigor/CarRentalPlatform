from psycopg2.extras import DateTimeTZRange
from rest_framework import serializers
from .enums import BookingStatus
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
        data["period"] = DateTimeTZRange(data["period_start"], data["period_end"])
        return data


class BookingUpdateSerializer(serializers.Serializer):
    pickup_station_id = serializers.IntegerField(required=False)
    dropoff_station_id = serializers.IntegerField(required=False)
    period_start = serializers.DateTimeField(required=False)
    period_end = serializers.DateTimeField(required=False)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    status = serializers.ChoiceField(choices=BookingStatus.choices, required=False)

    def validate(self, data):
        period_start = data.pop("period_start", None)
        period_end = data.pop("period_end", None)
        if period_start is not None and period_end is not None:
            if period_start >= period_end:
                raise serializers.ValidationError(
                    {"period_end": "period_end must be after period_start"}
                )
            data["period"] = DateTimeTZRange(period_start, period_end)
        elif period_start is not None or period_end is not None:
            raise serializers.ValidationError(
                "Both period_start and period_end are required to update the period."
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