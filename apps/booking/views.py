from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import Customer
from apps.booking.models import Booking
from apps.booking.serializers import (
    BookingCreateSerializer,
    BookingUpdateSerializer,
    BookingDetailSerializer,
)
from apps.booking.services import BookingService
from apps.booking.utils import require_idempotency_key
from root.exceptions import PermissionDeniedError


class BookingViewSet(ModelViewSet):
    """
    list           GET    /api/v1/bookings/             — list (filter: ?customer_id= ?status= ?car_id=)
    create         POST   /api/v1/bookings/             — create (idempotent)
    retrieve       GET    /api/v1/bookings/{id}/        — detail
    update         PUT    /api/v1/bookings/{id}/        — full update
    partial_update PATCH  /api/v1/bookings/{id}/        — partial update
    destroy        DELETE /api/v1/bookings/{id}/        — delete
    cancel         POST   /api/v1/bookings/{id}/cancel/ — cancel
    """

    queryset = Booking.objects.select_related(
        "customer", "car", "pickup_station", "dropoff_station"
    )
    serializer_class = BookingDetailSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        if self.action in ("update", "partial_update"):
            return BookingUpdateSerializer
        return BookingDetailSerializer

    def list(self, request, *args, **kwargs):
        customer_id = request.query_params.get("customer_id")
        status = request.query_params.get("status")
        car_id = request.query_params.get("car_id")
        bookings = BookingService().list_bookings(
            customer_id=int(customer_id) if customer_id else None,
            status=status or None,
            car_id=int(car_id) if car_id else None,
        )
        return Response(BookingDetailSerializer(bookings, many=True).data)

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

    def retrieve(self, request, *args, **kwargs):
        booking = BookingService().get_booking(booking_id=kwargs["id"])
        return Response(BookingDetailSerializer(booking).data)

    def update(self, request, *args, **kwargs):
        s = BookingUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        booking = BookingService().update_booking(booking_id=kwargs["id"], **s.validated_data)
        return Response(BookingDetailSerializer(booking).data)

    def partial_update(self, request, *args, **kwargs):
        s = BookingUpdateSerializer(data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        booking = BookingService().update_booking(booking_id=kwargs["id"], **s.validated_data)
        return Response(BookingDetailSerializer(booking).data)

    def destroy(self, request, *args, **kwargs):
        BookingService().delete_booking(booking_id=kwargs["id"])
        return Response(status=204)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, **kwargs):
        try:
            customer = Customer.objects.get(user_id=request.user.pk)
        except Customer.DoesNotExist:
            raise PermissionDeniedError()
        booking = BookingService().cancel_booking(
            booking_id=kwargs["id"], customer=customer
        )
        return Response(BookingDetailSerializer(booking).data)
