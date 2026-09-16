from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from .models import Car


class CarAvailabilitySerializer(serializers.Serializer):
    period_from = serializers.DateTimeField(source="from")
    period_to = serializers.DateTimeField(source="to")


class CarAvailabilityQuerySerializer(serializers.Serializer):
    period_from = serializers.DateTimeField()
    period_to = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["period_from"] >= attrs["period_to"]:
            raise serializers.ValidationError(
                _("`to` qiymati `from`dan katta bo'lishi kerak")
            )
        return attrs


class CarSearchQuerySerializer(serializers.Serializer):
    SORT_CHOICES = ("distance", "price")

    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    radius_m = serializers.IntegerField(min_value=1, max_value=50_000, default=5_000)
    date_from = serializers.DateTimeField(source="from")
    date_to = serializers.DateTimeField(source="to")
    model = serializers.CharField(required=False, allow_blank=True, max_length=200)
    sort = serializers.ChoiceField(choices=SORT_CHOICES, default="distance")

    def validate(self, attrs):
        if attrs["from"] >= attrs["to"]:
            raise serializers.ValidationError("`from` must be earlier than `to`.")
        return attrs


class CarSearchResultSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source="carModel.brand", read_only=True)
    model_name = serializers.CharField(source="carModel.model", read_only=True)
    seats = serializers.IntegerField(source="carModel.seats", read_only=True)
    transmission = serializers.CharField(source="carModel.transmission", read_only=True)
    fuel_type = serializers.CharField(source="carModel.fuel_type", read_only=True)
    daily_base_price = serializers.DecimalField(
        source="carModel.daily_base_price", max_digits=10, decimal_places=2, read_only=True
    )
    station_id = serializers.IntegerField(source="station.id", read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True)
    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    distance_m = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            "id",
            "plate",
            "brand",
            "model_name",
            "seats",
            "transmission",
            "fuel_type",
            "station_id",
            "station_name",
            "lat",
            "lon",
            "distance_m",
            "daily_base_price",
            "year",
            "odometer_km",
            "fuel_level",
        ]
        read_only_fields = fields

    def get_lat(self, obj) -> float:
        return obj.current_location.y

    def get_lon(self, obj) -> float:
        return obj.current_location.x

    def get_distance_m(self, obj) -> float:
        return round(obj.distance.m, 1)
