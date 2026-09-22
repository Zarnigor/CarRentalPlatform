from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Station
from .selectors import find_nearby_stations
from .serializers import NearbyStationsQuerySerializer, StationNearbySerializer


class StationViewSet(GenericViewSet):
    """GET  api/v1/stations/nearby/"""

    queryset = Station.objects.select_related("city")
    serializer_class = StationNearbySerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"], url_path="nearby", permission_classes=[AllowAny])
    def nearby(self, request):
        query = NearbyStationsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        stations = find_nearby_stations(**query.validated_data)
        return Response(StationNearbySerializer(stations, many=True).data)
