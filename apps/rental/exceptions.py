from django.utils.translation import gettext_lazy as _
from root.exceptions import NotFoundError, ConflictError, UnprocessableEntityError


class RentalNotFoundError(NotFoundError):
    default_message = _("Rental topilmadi")
    error_code = "rental_not_found"

    def __init__(self, rental_id=None, **extra):
        super().__init__(rental_id=rental_id, **extra)


class RentalInvalidStateError(ConflictError):
    default_message = _("Rental hozirgi holatda bu amalni bajarish mumkin emas")
    error_code = "rental_invalid_state"

    def __init__(self, rental_id=None, current_status=None, **extra):
        super().__init__(rental_id=rental_id, current_status=current_status, **extra)


class InvalidDropoffLocationError(UnprocessableEntityError):
    default_message = _("Mashinani qaytarish joyi geofence ichida emas")
    error_code = "invalid_dropoff_location"

    def __init__(self, rental_id=None, lat=None, lon=None, **extra):
        super().__init__(rental_id=rental_id, lat=lat, lon=lon, **extra)


class DamageRecordInvalidError(UnprocessableEntityError):
    default_message = _("Zarar (damage) ma'lumotlari noto'g'ri")
    error_code = "damage_record_invalid"


class PricingRuleNotFoundError(NotFoundError):
    default_message = _("Narx qoidasi (pricing rule) topilmadi")
    error_code = "pricing_rule_not_found"

    def __init__(self, car_model_id=None, **extra):
        super().__init__(car_model_id=car_model_id, **extra)
