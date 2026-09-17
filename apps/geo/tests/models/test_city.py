import pytest

from django.contrib.gis.geos import MultiPolygon, Polygon

from apps.geo.models import City


def _square(lon: float, lat: float, d: float = 0.5) -> Polygon:
    return Polygon(
        (
            (lon - d, lat - d), (lon + d, lat - d),
            (lon + d, lat + d), (lon - d, lat + d),
            (lon - d, lat - d),
        ),
        srid=4326,
    )


@pytest.mark.django_db
class TestCity:

    def test_creates_city(self):
        boundary = MultiPolygon(_square(69.2, 41.3), srid=4326)
        city = City.objects.create(
            name="Toshkent",
            timezone="Asia/Tashkent",
            boundary=boundary,
        )
        assert city.pk is not None

    def test_name_persists(self):
        boundary = MultiPolygon(_square(60.0, 40.0), srid=4326)
        city = City.objects.create(name="Samarqand", timezone="Asia/Tashkent", boundary=boundary)
        city.refresh_from_db()
        assert city.name == "Samarqand"

    def test_boundary_is_multipolygon(self):
        boundary = MultiPolygon(_square(55.0, 38.0), srid=4326)
        city = City.objects.create(name="Andijon", timezone="Asia/Tashkent", boundary=boundary)
        city.refresh_from_db()
        assert city.boundary.geom_type == "MultiPolygon"

    def test_name_max_length(self):
        field = City._meta.get_field("name")
        assert field.max_length == 30

    def test_timezone_max_length(self):
        field = City._meta.get_field("timezone")
        assert field.max_length == 30
