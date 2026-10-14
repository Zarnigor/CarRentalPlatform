from decimal import Decimal

from apps.fleet.serializers.car_model import CarModelWriteSerializer


class TestCarModelWriteSerializerValidation:

    def _base(self, **overrides):
        data = {
            "brand": "Chevrolet",
            "model": "Lacetti",
            "seats": 5,
            "transmission": "MANUAL",
            "fuel_type": "PETROL",
            "daily_base_price": "150000.00",
        }
        data.update(overrides)
        return data

    def test_valid_data_passes(self):
        s = CarModelWriteSerializer(data=self._base())
        assert s.is_valid(), s.errors

    def test_seats_zero_rejected(self):
        s = CarModelWriteSerializer(data=self._base(seats=0))
        assert not s.is_valid()
        assert "seats" in s.errors

    def test_seats_negative_rejected(self):
        s = CarModelWriteSerializer(data=self._base(seats=-1))
        assert not s.is_valid()
        assert "seats" in s.errors

    def test_seats_one_accepted(self):
        s = CarModelWriteSerializer(data=self._base(seats=1))
        assert s.is_valid(), s.errors

    def test_daily_base_price_zero_rejected(self):
        s = CarModelWriteSerializer(data=self._base(daily_base_price="0.00"))
        assert not s.is_valid()
        assert "daily_base_price" in s.errors

    def test_daily_base_price_negative_rejected(self):
        s = CarModelWriteSerializer(data=self._base(daily_base_price="-100.00"))
        assert not s.is_valid()
        assert "daily_base_price" in s.errors

    def test_daily_base_price_positive_accepted(self):
        s = CarModelWriteSerializer(data=self._base(daily_base_price="0.01"))
        assert s.is_valid(), s.errors
