from rest_framework import serializers

from .models import Station


class NearbyStationsQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    limit = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)


class StationNearbySerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    distance_m = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = ["id", "name", "city_name", "lat", "lon", "capacity", "target_count", "distance_m"]
        read_only_fields = fields

    def get_lat(self, obj) -> float:
        return obj.location.y

    def get_lon(self, obj) -> float:
        return obj.location.x

    def get_distance_m(self, obj) -> float:
        return round(obj.distance.m, 1)  # obj.distance set by Distance annotation in selector