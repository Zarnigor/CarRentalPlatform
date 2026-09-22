import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.contrib.gis.geos import Point, Polygon, MultiPolygon

from psycopg2.extras import DateTimeTZRange

from apps.accounts.models import CustomUser, Customer
from apps.booking.enums import BookingStatus
from apps.booking.models import Booking, PricingRule
from apps.fleet.models import Car, CarModel
from apps.fleet.enums import CarStatus
from apps.geo.models import City, Station


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_square_polygon(lon: float, lat: float, delta: float = 0.5) -> Polygon:
    """Return a simple square PolygonField value centred on (lon, lat)."""
    coords = (
        (lon - delta, lat - delta),
        (lon + delta, lat - delta),
        (lon + delta, lat + delta),
        (lon - delta, lat + delta),
        (lon - delta, lat - delta),  # close the ring
    )
    return Polygon(coords, srid=4326)


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def city(db) -> City:
    boundary = MultiPolygon(_make_square_polygon(41.3, 69.2, delta=1.0), srid=4326)
    return City.objects.create(name="Toshkent", timezone="Asia/Tashkent", boundary=boundary)


@pytest.fixture
def station(city) -> Station:
    loc = Point(69.2401, 41.2995, srid=4326)
    geofence = _make_square_polygon(69.2401, 41.2995, delta=0.05)
    return Station.objects.create(
        city=city,
        name="Chilonzor",
        location=loc,
        capacity=20,
        geofence=geofence,
        target_count=15,
    )


@pytest.fixture
def car_model() -> CarModel:
    return CarModel.objects.create(
        brand="Chevrolet",
        model="Lacetti",
        seats=5,
        daily_base_price=Decimal("150000.00"),
    )


@pytest.fixture
def pricing_rule() -> PricingRule:
    from apps.booking.enums import PricingScope, PricingRuleType
    valid = DateTimeTZRange(
        _utc(2024, 1, 1),
        _utc(2030, 1, 1),
    )
    return PricingRule.objects.create(
        name="Standard",
        scope=PricingScope.GLOBAL,
        rule_type=PricingRuleType.SEASONAL,
        priority=0,
        valid_period=valid,
        multiplier=1,
        flat_fee=Decimal("0.00"),
        price_per_day=Decimal("150000.00"),
        free_km_per_day=100,
        price_per_extra_km=Decimal("500.00"),
    )


@pytest.fixture
def car(car_model, station) -> Car:
    return Car.objects.create(
        carModel=car_model,
        plate="01A123BC",
        station=station,
        status=CarStatus.AVAILABLE,
        current_location=Point(69.2401, 41.2995, srid=4326),
        odometer_km=10000,
        fuel_level=80,
        year=2020,
    )


@pytest.fixture
def django_user() -> CustomUser:
    return CustomUser.objects.create_user(
        username="testdriver",
        password="secret",
        email="driver@test.com",
    )


@pytest.fixture
def customer(django_user) -> Customer:
    from datetime import date
    return Customer.objects.create(
        user=django_user,
        license_no="AA1234567",
        license_verified_at=date(2023, 1, 1),
        risk_score=0.0,
    )


@pytest.fixture
def booking_period() -> DateTimeTZRange:
    now = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
    return DateTimeTZRange(now + timedelta(hours=1), now + timedelta(hours=5))


@pytest.fixture
def confirmed_booking(customer, car, station, booking_period, pricing_rule) -> Booking:
    """A booking already in CONFIRMED state, ready for rental start."""
    return Booking.objects.create(
        customer=customer,
        car=car,
        pickup_station=station,
        dropoff_station=station,
        pricing_rule=pricing_rule,
        period=booking_period,
        status=BookingStatus.CONFIRMED,
        total_price=Decimal("600000.00"),
    )
