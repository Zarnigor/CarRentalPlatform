from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import find_nearby_stations
from .serializers import NearbyStationsQuerySerializer, StationNearbySerializer


class NearbyStationsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = NearbyStationsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        stations = find_nearby_stations(**query.validated_data)
        return Response(StationNearbySerializer(stations, many=True).data)