import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon

from apps.geo.serializers.city import CitySerializer


def _square(lon=69.2, lat=41.3, d=0.5):
    return Polygon((
        (lon - d, lat - d), (lon + d, lat - d),
        (lon + d, lat + d), (lon - d, lat + d),
        (lon - d, lat - d),
    ), srid=4326)


def _boundary():
    return MultiPolygon(_square(), srid=4326)


class TestCitySerializerValidateTimezone:

    @pytest.mark.django_db
    def test_valid_timezone_accepted(self):
        s = CitySerializer(data={
            "name": "Toshkent",
            "timezone": "Asia/Tashkent",
            "boundary": _boundary(),
        })
        assert s.is_valid(), s.errors

    def test_invalid_timezone_rejected(self):
        s = CitySerializer(data={
            "name": "Toshkent",
            "timezone": "Fake/Zone",
            "boundary": _boundary(),
        })
        assert not s.is_valid()
        assert "timezone" in s.errors

    def test_empty_timezone_rejected(self):
        s = CitySerializer(data={
            "name": "Toshkent",
            "timezone": "",
            "boundary": _boundary(),
        })
        assert not s.is_valid()
        assert "timezone" in s.errors


class TestCitySerializerValidateBoundary:

    @pytest.mark.django_db
    def test_multipolygon_accepted(self):
        s = CitySerializer(data={
            "name": "Toshkent",
            "timezone": "Asia/Tashkent",
            "boundary": _boundary(),
        })
        assert s.is_valid(), s.errors

    @pytest.mark.django_db
    def test_polygon_auto_converted_to_multipolygon(self):
        s = CitySerializer(data={
            "name": "Samarqand",
            "timezone": "Asia/Tashkent",
            "boundary": _square(),
        })
        assert s.is_valid(), s.errors
        assert isinstance(s.validated_data["boundary"], MultiPolygon)

    @pytest.mark.django_db
    def test_boundary_srid_set_to_4326_when_missing(self):
        poly = _square()
        poly.srid = None
        mp = MultiPolygon(poly)
        mp.srid = None
        s = CitySerializer(data={
            "name": "Andijon",
            "timezone": "Asia/Tashkent",
            "boundary": mp,
        })
        assert s.is_valid(), s.errors
        assert s.validated_data["boundary"].srid == 4326
