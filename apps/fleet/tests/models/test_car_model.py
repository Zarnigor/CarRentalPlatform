import pytest
from decimal import Decimal

from apps.fleet.enums import FuelType, TransmissionType
from apps.fleet.models import CarModel


@pytest.mark.django_db
class TestCarModel:

    def test_creates_car_model(self):
        cm = CarModel.objects.create(
            brand="Chevrolet",
            model="Lacetti",
            seats=5,
            daily_base_price=Decimal("150000.00"),
        )
        assert cm.pk is not None

    def test_str_returns_brand_and_model(self):
        cm = CarModel.objects.create(
            brand="Daewoo",
            model="Nexia",
            seats=5,
            daily_base_price=Decimal("100000.00"),
        )
        assert str(cm) == "Daewoo Nexia"

    def test_transmission_defaults_to_manual(self):
        cm = CarModel.objects.create(
            brand="Toyota",
            model="Corolla",
            seats=5,
            daily_base_price=Decimal("200000.00"),
        )
        assert cm.transmission == TransmissionType.MANUAL

    def test_fuel_type_defaults_to_petrol(self):
        cm = CarModel.objects.create(
            brand="Kia",
            model="Rio",
            seats=5,
            daily_base_price=Decimal("180000.00"),
        )
        assert cm.fuel_type == FuelType.PETROL

    def test_all_fuel_types_valid(self):
        for i, fuel in enumerate(FuelType.values):
            cm = CarModel.objects.create(
                brand=f"Brand{i}",
                model=f"Model{i}",
                seats=5,
                daily_base_price=Decimal("100000.00"),
                fuel_type=fuel,
            )
            assert cm.fuel_type == fuel

    def test_all_transmission_types_valid(self):
        for i, trans in enumerate(TransmissionType.values):
            cm = CarModel.objects.create(
                brand=f"TB{i}",
                model=f"TM{i}",
                seats=5,
                daily_base_price=Decimal("100000.00"),
                transmission=trans,
            )
            assert cm.transmission == trans

    def test_brand_max_length(self):
        field = CarModel._meta.get_field("brand")
        assert field.max_length == 200

    def test_model_max_length(self):
        field = CarModel._meta.get_field("model")
        assert field.max_length == 200
