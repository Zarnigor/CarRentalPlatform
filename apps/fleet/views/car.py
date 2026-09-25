from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.booking.selectors import BookingSelector
from apps.fleet.models import Car
from apps.fleet.selectors import find_available_cars, get_car_or_raise
from apps.fleet.serializers import (
    CarAvailabilityQuerySerializer,
    CarAvailabilitySerializer,
    CarReadSerializer,
    CarSearchQuerySerializer,
    CarSearchResultSerializer,
    CarWriteSerializer,
)


class CarViewSet(ModelViewSet):
    """
    GET    cars/                    — list
    POST   cars/                    — create
    GET    cars/{pk}/                — retrieve
    PUT    cars/{pk}/                — full update
    PATCH  cars/{pk}/                — partial update
    DELETE cars/{pk}/                — delete
    ...
    GET    cars/{pk}/availability/   — availability check
    GET    cars/search/              — search available cars
    """

    queryset = Car.objects.select_related("carModel", "station")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CarWriteSerializer
        if self.action == "search":
            return CarSearchResultSerializer
        return CarReadSerializer

    @action(
        detail=True,
        methods=["get"],
        url_path="availability",
        permission_classes=[AllowAny],
    )
    def availability(self, request, pk=None):
        get_car_or_raise(int(pk))
        query = CarAvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        available = BookingSelector().check_availability(
            car_id=int(pk), period=query.validated_data["period"]
        )
        return Response(CarAvailabilitySerializer({"available": available}).data)

    @action(
        detail=False, methods=["get"], url_path="search", permission_classes=[AllowAny]
    )
    def search(self, request):
        query = CarSearchQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        cars = find_available_cars(
            lat=data["lat"],
            lon=data["lon"],
            radius_m=data["radius_m"],
            date_from=data["from"],
            date_to=data["to"],
            model=data.get("model"),
            sort=data["sort"],
        )
        return Response(CarSearchResultSerializer(cars, many=True).data)
