from rest_framework import serializers

from apps.fleet.models import CarModel


class CarModelReadSerializer(serializers.ModelSerializer):
    transmission_display = serializers.CharField(source="get_transmission_display", read_only=True)
    fuel_type_display = serializers.CharField(source="get_fuel_type_display", read_only=True)

    class Meta:
        model = CarModel
        fields = [
            "id",
            "brand",
            "model",
            "seats",
            "transmission",
            "transmission_display",
            "fuel_type",
            "fuel_type_display",
            "daily_base_price",
        ]
        read_only_fields = fields


class CarModelWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarModel
        fields = [
            "id",
            "brand",
            "model",
            "seats",
            "transmission",
            "fuel_type",
            "daily_base_price",
        ]
        read_only_fields = ["id"]

    def validate_seats(self, value):
        if value < 1:
            raise serializers.ValidationError("seats kamida 1 bo'lishi kerak.")
        return value

    def validate_daily_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("daily_base_price musbat bo'lishi kerak.")
        return value