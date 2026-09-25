from django.utils.translation import gettext_lazy as _
from psycopg2.extras import DateTimeTZRange
from rest_framework import serializers

from apps.fleet.models import Car
from .car_model import CarModelReadSerializer


class CarAvailabilitySerializer(serializers.Serializer):
    available = serializers.BooleanField()


class CarAvailabilityQuerySerializer(serializers.Serializer):
    period_from = serializers.DateTimeField()
    period_to = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["period_from"] >= attrs["period_to"]:
            raise serializers.ValidationError(
                _("`to` qiymati `from`dan katta bo'lishi kerak")
            )
        attrs["period"] = DateTimeTZRange(attrs["period_from"], attrs["period_to"])
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


class CarReadSerializer(serializers.ModelSerializer):
    carModel = CarModelReadSerializer(read_only=True)
    longitude = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            "id",
            "carModel",
            "plate",
            "station",
            "status",
            "longitude",
            "latitude",
            "odometer_km",
            "fuel_level",
            "year",
        ]
        read_only_fields = fields

    def get_longitude(self, obj):
        return obj.current_location.x if obj.current_location else None

    def get_latitude(self, obj):
        return obj.current_location.y if obj.current_location else None


class CarSearchResultSerializer(CarReadSerializer):
    """CarReadSerializer + qidiruvga xos station_name va distance_m maydonlari."""

    station_name = serializers.CharField(source="station.name", read_only=True)
    distance_m = serializers.SerializerMethodField()

    class Meta(CarReadSerializer.Meta):
        fields = CarReadSerializer.Meta.fields + ["station_name", "distance_m"]
        read_only_fields = fields

    def get_distance_m(self, obj):
        return round(obj.distance.m, 1)


class CarWriteSerializer(serializers.ModelSerializer):
    longitude = serializers.FloatField(write_only=True)
    latitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Car
        fields = [
            "id",
            "carModel",
            "plate",
            "station",
            "status",
            "odometer_km",
            "fuel_level",
            "year",
            "longitude",
            "latitude",
        ]
        read_only_fields = ["id"]

    def validate_fuel_level(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError(
                "fuel_level 0 dan 100 gacha bo'lishi kerak."
            )
        return value

    def validate_odometer_km(self, value):
        if value < 0:
            raise serializers.ValidationError("odometer_km manfiy bo'la olmaydi.")
        return value

    def validate_year(self, value):
        if value < 1990:
            raise serializers.ValidationError("year 1990 dan katta bo'lishi kerak.")
        return value

    def create(self, validated_data):
        from django.contrib.gis.geos import Point

        lon = validated_data.pop("longitude")
        lat = validated_data.pop("latitude")
        validated_data["current_location"] = Point(lon, lat, srid=4326)
        return Car.objects.create(**validated_data)

    def update(self, instance, validated_data):
        from django.contrib.gis.geos import Point

        lon = validated_data.pop("longitude", None)
        lat = validated_data.pop("latitude", None)
        if lon is not None and lat is not None:
            instance.current_location = Point(lon, lat, srid=4326)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance