import pytest
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.db import IntegrityError

from apps.fleet.enums import CarStatus
from apps.fleet.models import Car


@pytest.mark.django_db
class TestCar:

    def test_creates_car(self, car):
        assert car.pk is not None

    def test_str_returns_plate(self, car):
        assert str(car) == car.plate

    def test_status_defaults_to_available(self, car_model, station):
        car = Car.objects.create(
            carModel=car_model,
            plate="99X999XX",
            station=station,
            current_location=Point(69.24, 41.29, srid=4326),
            odometer_km=0,
            fuel_level=100,
            year=2022,
        )
        assert car.status == CarStatus.AVAILABLE

    def test_plate_is_unique(self, car_model, station):
        Car.objects.create(
            carModel=car_model,
            plate="UNIQUE01",
            station=station,
            current_location=Point(69.24, 41.29, srid=4326),
            odometer_km=0,
            fuel_level=100,
            year=2021,
        )
        with pytest.raises(IntegrityError):
            Car.objects.create(
                carModel=car_model,
                plate="UNIQUE01",
                station=station,
                current_location=Point(69.30, 41.30, srid=4326),
                odometer_km=500,
                fuel_level=80,
                year=2021,
            )

    def test_current_location_is_point(self, car):
        car.refresh_from_db()
        assert car.current_location.geom_type == "Point"

    def test_current_location_srid(self, car):
        car.refresh_from_db()
        assert car.current_location.srid == 4326

    def test_all_car_statuses_valid(self, car_model, station):
        for i, status in enumerate(CarStatus.values):
            c = Car.objects.create(
                carModel=car_model,
                plate=f"ST{i:04d}XX",
                station=station,
                status=status,
                current_location=Point(69.24, 41.29, srid=4326),
                odometer_km=0,
                fuel_level=100,
                year=2020,
            )
            assert c.status == status

    def test_cascade_delete_with_car_model(self, car_model, station):
        Car.objects.create(
            carModel=car_model,
            plate="DEL00001",
            station=station,
            current_location=Point(69.24, 41.29, srid=4326),
            odometer_km=0,
            fuel_level=100,
            year=2020,
        )
        car_model.delete()
        assert Car.objects.filter(plate="DEL00001").count() == 0

    def test_station_index_exists(self):
        index_names = [idx.name for idx in Car._meta.indexes]
        assert "car_station_fk" in index_names
