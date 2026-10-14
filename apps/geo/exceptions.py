from root.exceptions import NotFoundError, ValidationError
from django.utils.translation import gettext_lazy as _

class CityNotFoundError(NotFoundError):
    default_message = "Shahar topilmadi"
    error_code = "city_not_found"

    def __init__(self, city_id=None, **extra):
        super().__init__(city_id=city_id, **extra)


class StationNotFoundError(NotFoundError):
    default_message = "Stansiya topilmadi"
    error_code = "station_not_found"

    def __init__(self, station_id=None, **extra):
        super().__init__(station_id=station_id, **extra)


class InvalidCoordinatesError(ValidationError):
    """lat/lon qiymatlari yaroqsiz yoki yo'q (masalan lat > 90, yoki umuman berilmagan)."""
    default_message = "Koordinatalar (lat/lon) yaroqsiz"
    error_code = "invalid_coordinates"


class InvalidBoundaryError(ValidationError):
    default_message =  _("Geometry turi Polygon yoki MultiPolygon bo'lishi kerak.")
    error_code = 'invalid_boundary'

