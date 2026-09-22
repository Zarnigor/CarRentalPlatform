from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from .models import Booking
from .serializers import BookingCreateSerializer, BookingDetailSerializer
from .services import BookingService
from .utils import require_idempotency_key


class BookingViewSet(CreateModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    POST  api/v1/bookings/         — create (idempotent)
    GET   api/v1/bookings/{id}/    — retrieve
    """

    queryset = Booking.objects.select_related(
        "customer", "car", "pickup_station", "dropoff_station"
    )
    serializer_class = BookingDetailSerializer
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingDetailSerializer

    def create(self, request, *args, **kwargs):
        key = require_idempotency_key(request)
        s = BookingCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        booking, is_replay = BookingService().create_booking_from_user(
            user=request.user, idempotency_key=key, **s.validated_data
        )
        resp = Response(BookingDetailSerializer(booking).data, status=200 if is_replay else 201)
        if is_replay:
            resp["Idempotency-Replayed"] = "true"
        return resp



