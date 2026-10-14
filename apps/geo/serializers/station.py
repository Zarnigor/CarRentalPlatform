from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from apps.geo.models import Station


class NearbyStationsQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    limit = serializers.IntegerField(
        required=False, default=10, min_value=1, max_value=50
    )



class StationSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    location = GeometryField()
    geofence = GeometryField()

    class Meta:
        model = Station
        fields = [
            "id",
            "name",
            "city",
            "city_name",
            "location",
            "geofence",
            "capacity",
            "target_count",
        ]
        read_only_fields = ["id"]

        def get_lat(self, obj) -> float | None:
            return obj.location.y

        def get_lon(self, obj) -> float | None:
            return obj.location.x


class StationNearbySerializer(StationSerializer):
    distance_m = serializers.SerializerMethodField()

    class Meta(StationSerializer.Meta):
        fields = StationSerializer.Meta.fields + ["distance_m"]
        read_only_fields = fields

    def get_distance_m(self, obj) -> float:
        return round(obj.distance.m, 1)
