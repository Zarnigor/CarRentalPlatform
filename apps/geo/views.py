from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.geo.models import City, Station
from apps.geo.selectors import find_nearby_stations
from apps.geo.serializers import (
    CitySerializer,
    NearbyStationsQuerySerializer,
    StationNearbySerializer,
    StationSerializer,
)


class StationNearbyViewSet(GenericViewSet):
    """GET  api/stations/nearby/"""

    queryset = Station.objects.select_related("city")
    serializer_class = StationNearbySerializer
    permission_classes = [AllowAny]

    @extend_schema(parameters=[NearbyStationsQuerySerializer])
    @action(
        detail=False, methods=["get"], url_path="nearby", permission_classes=[AllowAny]
    )
    def nearby(self, request):
        query = NearbyStationsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        stations = find_nearby_stations(**query.validated_data)
        return Response(StationNearbySerializer(stations, many=True).data)


class CityViewSet(ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer


class StationViewSet(ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
