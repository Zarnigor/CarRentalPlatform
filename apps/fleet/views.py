from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.selectors import check_availability

from .selectors import get_car_or_raise
from .serializers import CarAvailabilityQuerySerializer, CarAvailabilitySerializer


class CarAvailabilityView(APIView):
    """GET /cars/{id}/availability?from=&to= - auth talab qilinmaydi."""

    permission_classes = [AllowAny]

    def get(self, request, car_id: int):
        get_car_or_raise(car_id)
        query = CarAvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        available = check_availability(car_id=car_id, **query.validated_data)
        return Response(CarAvailabilitySerializer({"available": available}).data)