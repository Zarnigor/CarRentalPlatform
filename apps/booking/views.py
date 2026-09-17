from psycopg2.extras import DateTimeTZRange
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Customer
from root.exceptions import PermissionDeniedError

from .exceptions import MissingIdempotencyKeyError
from .models import Booking
from .serializers import BookingCreateSerializer, BookingDetailSerializer
from .services import BookingService


def _require_idempotency_key(request) -> str:
    key = request.headers.get("Idempotency-Key")
    if not key:
        raise MissingIdempotencyKeyError()
    return key


def _get_customer(request) -> Customer:
    try:
        return Customer.objects.get(user_id=request.user.pk)
    except Customer.DoesNotExist:
        raise PermissionDeniedError()


class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key = _require_idempotency_key(request)
        body = BookingCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        d = body.validated_data

        is_replay = Booking.objects.filter(idempotency_key=key).exists()
        booking = BookingService().create_booking(
            customer=_get_customer(request),
            car_id=d["car_id"],
            pickup_station_id=d["pickup_station_id"],
            dropoff_station_id=d["dropoff_station_id"],
            period=DateTimeTZRange(d["period_start"], d["period_end"]),
            total_price=d["total_price"],
            idempotency_key=key,
        )

        resp = Response(BookingDetailSerializer(booking).data, status=200 if is_replay else 201)
        if is_replay:
            resp["Idempotency-Replayed"] = "true"
        return resp


class BookingDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingDetailSerializer
    queryset = Booking.objects.select_related("customer", "car", "pickup_station", "dropoff_station")
    lookup_field = "id"
