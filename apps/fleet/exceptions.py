from root.exceptions import NotFoundError, ConflictError
from django.utils.translation import gettext_lazy as _

class CarModelNotFoundError(NotFoundError):
    default_message = _("Mashina modeli topilmadi")
    error_code = "car_model_not_found"

    def __init__(self, car_model_id=None, **extra):
        super().__init__(car_model_id=car_model_id, **extra)


class CarNotFoundError(NotFoundError):
    default_message = _("Mashina topilmadi")
    error_code = "car_not_found"

    def __init__(self, car_id=None, **extra):
        super().__init__(car_id=car_id, **extra)


class CarNotAvailableError(ConflictError):
    default_message = _("Mashina hozir band yoki texnik ko'rikda")
    error_code = "car_not_available"

    def __init__(self, car_id=None, current_status=None, **extra):
        super().__init__(car_id=car_id, current_status=current_status, **extra)
