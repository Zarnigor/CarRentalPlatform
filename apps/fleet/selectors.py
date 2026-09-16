from .enums import CarStatus
from .exceptions import CarNotFoundError
from .models import Car

from datetime import datetime
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Exists, OuterRef, QuerySet
from ..booking.models import Booking
from ..booking.enums import BookingStatus


def get_car_or_raise(car_id: int) -> Car:
    try:
        return Car.objects.get(id=car_id)
    except Car.DoesNotExist:
        raise CarNotFoundError(car_id=car_id)


def find_available_cars(
    lat: float,
    lon: float,
    radius_m: int,
    date_from: datetime,
    date_to: datetime,
    model: str | None = None,
    sort: str = "distance",
) -> QuerySet[Car]:
    """Search for cars available in a given radius and time window.

    Args:
        lat: Latitude of the search origin.
        lon: Longitude of the search origin.
        radius_m: Search radius in meters.
        date_from: Start of the requested rental window.
        date_to: End of the requested rental window.
        model: Optional CarModel `brand` or `model` name filter (partial match).
        sort: "distance" or "price" — determines ordering.

    Returns:
        QuerySet of Car annotated with `distance` (meters), filtered to
        AVAILABLE cars with no overlapping active booking in the requested
        window, ordered by distance or price.
    """
    origin = Point(lon, lat, srid=4326)

    blocking_statuses = [
        BookingStatus.PENDING,
        BookingStatus.CONFIRMED,
        BookingStatus.ACTIVE,
        BookingStatus.PAYMENT_PENDING,
    ]

    overlapping_bookings = Booking.objects.filter(
        car=OuterRef("pk"),
        status__in=blocking_statuses,
        start_at__lt=date_to,
        end_at__gt=date_from,
    )

    queryset = (
        Car.objects.select_related("carModel", "station")
        .annotate(distance=Distance("current_location", origin))
        .filter(status=CarStatus.AVAILABLE, distance__lte=radius_m)
        .annotate(has_overlap=Exists(overlapping_bookings))
        .filter(has_overlap=False)
    )

    if model:
        queryset = queryset.filter(
            models_q_brand_or_model(model)
        )

    if sort == "price":
        queryset = queryset.order_by("carModel__daily_base_price", "distance")
    else:
        queryset = queryset.order_by("distance", "carModel__daily_base_price")

    return queryset


def models_q_brand_or_model(term: str):
    from django.db.models import Q

    return Q(carModel__brand__icontains=term) | Q(carModel__model__icontains=term)