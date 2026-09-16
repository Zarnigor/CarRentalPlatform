from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.booking.selectors import BookingSelector
from .selectors import get_car_or_raise, find_available_cars
from .serializers import (
    CarAvailabilityQuerySerializer, CarAvailabilitySerializer,
    CarSearchQuerySerializer, CarSearchResultSerializer
)


class CarAvailabilityView(APIView):
    """GET /cars/{id}/availability?from=&to= - auth talab qilinmaydi."""

    permission_classes = [AllowAny]

    def get(self, request, car_id: int):
        get_car_or_raise(car_id)
        query = CarAvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        available = BookingSelector.check_availability(car_id=car_id, **query.validated_data)
        return Response(CarAvailabilitySerializer({"available": available}).data)


class CarSearchView(APIView):
    """Search available cars near a point within a time window."""

    permission_classes = [AllowAny]

    def get(self, request):
        query = CarSearchQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data

        cars = find_available_cars(
            lat=data["lat"], lon=data["lon"], radius_m=data["radius_m"],
            date_from=data["from"], date_to=data["to"],
            model=data.get("model"), sort=data["sort"],
        )

        return Response(CarSearchResultSerializer(cars, many=True).data)