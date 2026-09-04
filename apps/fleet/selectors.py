from .exceptions import CarNotFoundError
from .models import Car


def get_car_or_raise(car_id: int) -> Car:
    try:
        return Car.objects.get(id=car_id)
    except Car.DoesNotExist:
        raise CarNotFoundError(car_id=car_id)