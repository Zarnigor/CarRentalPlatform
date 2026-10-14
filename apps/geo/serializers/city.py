from zoneinfo import available_timezones

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from apps.geo.exceptions import InvalidBoundaryError
from apps.geo.models import City



class CitySerializer(serializers.ModelSerializer):
    boundary = GeometryField()

    class Meta:
        model = City
        fields = ("id", "name", "timezone", "boundary")
        read_only_fields = ("id",)

    def validate_timezone(self, value):
        if value not in available_timezones():
            raise serializers.ValidationError(
                _("Noto'g'ri timezone (masalan: Asia/Tashkent).")
            )
        return value

    def validate_boundary(self, value):
        if isinstance(value, Polygon):
            value = MultiPolygon(value)
        if not isinstance(value, MultiPolygon):
            raise InvalidBoundaryError()
        if value.srid is None:
            value.srid = 4326
        if not value.valid:
            raise InvalidBoundaryError(
                _("Invalid geometry: %(reason)s") % {"reason": value.valid_reason},
                code="invalid_geometry",
            )
        return value
