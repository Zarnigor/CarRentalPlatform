import pytest

from django.contrib.gis.geos import MultiPolygon, Point, Polygon

from apps.geo.models import City, Station


def _square(lon: float, lat: float, d: float = 0.5) -> Polygon:
    return Polygon(
        (
            (lon - d, lat - d), (lon + d, lat - d),
            (lon + d, lat + d), (lon - d, lat + d),
            (lon - d, lat - d),
        ),
        srid=4326,
    )


@pytest.fixture
def city(db):
    boundary = MultiPolygon(_square(69.2, 41.3, d=1.0), srid=4326)
    return City.objects.create(name="TestCity", timezone="UTC", boundary=boundary)


@pytest.mark.django_db
class TestStation:

    def test_creates_station(self, city):
        station = Station.objects.create(
            city=city,
            name="North Hub",
            location=Point(69.24, 41.29, srid=4326),
            capacity=30,
            geofence=_square(69.24, 41.29, d=0.05),
            target_count=20,
        )
        assert station.pk is not None

    def test_location_is_point(self, city):
        station = Station.objects.create(
            city=city,
            name="East Hub",
            location=Point(69.35, 41.30, srid=4326),
            capacity=10,
            geofence=_square(69.35, 41.30, d=0.05),
            target_count=8,
        )
        station.refresh_from_db()
        assert station.location.geom_type == "Point"

    def test_geofence_is_polygon(self, city):
        station = Station.objects.create(
            city=city,
            name="West Hub",
            location=Point(69.10, 41.28, srid=4326),
            capacity=5,
            geofence=_square(69.10, 41.28, d=0.03),
            target_count=4,
        )
        station.refresh_from_db()
        assert station.geofence.geom_type == "Polygon"

    def test_cascade_delete_with_city(self, city):
        Station.objects.create(
            city=city,
            name="Temp Station",
            location=Point(69.20, 41.25, srid=4326),
            capacity=5,
            geofence=_square(69.20, 41.25, d=0.02),
            target_count=3,
        )
        city.delete()
        assert Station.objects.filter(name="Temp Station").count() == 0

    def test_name_max_length(self):
        field = Station._meta.get_field("name")
        assert field.max_length == 30
