import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.contrib.gis.geos import Point

from apps.fleet.serializers.car import (
    CarAvailabilityQuerySerializer,
    CarSearchQuerySerializer,
    CarReadSerializer,
    CarWriteSerializer,
)


def _utc(hours=0):
    return datetime(2025, 6, 1, tzinfo=timezone.utc) + timedelta(hours=hours)


# ── CarAvailabilityQuerySerializer ────────────────────────────────────────────

class TestCarAvailabilityQuerySerializer:

    def test_valid_builds_period_range(self):
        s = CarAvailabilityQuerySerializer(data={
            "period_from": _utc(0).isoformat(),
            "period_to": _utc(4).isoformat(),
        })
        assert s.is_valid(), s.errors
        assert s.validated_data["period"].lower == _utc(0)
        assert s.validated_data["period"].upper == _utc(4)

    def test_rejects_period_from_equal_to_period_to(self):
        s = CarAvailabilityQuerySerializer(data={
            "period_from": _utc(0).isoformat(),
            "period_to": _utc(0).isoformat(),
        })
        assert not s.is_valid()

    def test_rejects_period_from_after_period_to(self):
        s = CarAvailabilityQuerySerializer(data={
            "period_from": _utc(5).isoformat(),
            "period_to": _utc(2).isoformat(),
        })
        assert not s.is_valid()


# ── CarSearchQuerySerializer ──────────────────────────────────────────────────

class TestCarSearchQuerySerializer:

    def _valid_data(self, **overrides):
        data = {
            "lat": 41.3, "lon": 69.2,
            "date_from": _utc(0).isoformat(),
            "date_to": _utc(4).isoformat(),
        }
        data.update(overrides)
        return data

    def test_valid_data_passes(self):
        s = CarSearchQuerySerializer(data=self._valid_data())
        assert s.is_valid(), s.errors

    def test_rejects_from_equal_to_to(self):
        s = CarSearchQuerySerializer(data=self._valid_data(
            date_from=_utc(0).isoformat(), date_to=_utc(0).isoformat(),
        ))
        assert not s.is_valid()

    def test_rejects_from_after_to(self):
        s = CarSearchQuerySerializer(data=self._valid_data(
            date_from=_utc(5).isoformat(), date_to=_utc(2).isoformat(),
        ))
        assert not s.is_valid()

    def test_lat_out_of_range_rejected(self):
        s = CarSearchQuerySerializer(data=self._valid_data(lat=91.0))
        assert not s.is_valid()
        assert "lat" in s.errors

    def test_lon_out_of_range_rejected(self):
        s = CarSearchQuerySerializer(data=self._valid_data(lon=181.0))
        assert not s.is_valid()
        assert "lon" in s.errors

    def test_radius_m_defaults_to_5000(self):
        s = CarSearchQuerySerializer(data=self._valid_data())
        assert s.is_valid(), s.errors
        assert s.validated_data["radius_m"] == 5000

    def test_sort_defaults_to_distance(self):
        s = CarSearchQuerySerializer(data=self._valid_data())
        assert s.is_valid(), s.errors
        assert s.validated_data["sort"] == "distance"


# ── CarReadSerializer ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCarReadSerializer:

    def test_longitude_and_latitude_extracted(self, car):
        data = CarReadSerializer(car).data
        assert data["longitude"] == pytest.approx(car.current_location.x, abs=1e-6)
        assert data["latitude"] == pytest.approx(car.current_location.y, abs=1e-6)

    def test_longitude_none_when_no_location(self, car):
        car.current_location = None
        data = CarReadSerializer(car).data
        assert data["longitude"] is None
        assert data["latitude"] is None


# ── CarWriteSerializer ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCarWriteSerializerValidation:

    def _base(self, car_model, station, **overrides):
        data = {
            "carModel": car_model.pk,
            "plate": "99TEST99",
            "station": station.pk,
            "status": "AVAILABLE",
            "odometer_km": 1000,
            "fuel_level": 80,
            "year": 2020,
            "longitude": 69.2,
            "latitude": 41.3,
        }
        data.update(overrides)
        return data

    def test_valid_data_passes(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station))
        assert s.is_valid(), s.errors

    def test_fuel_level_above_100_rejected(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station, fuel_level=101))
        assert not s.is_valid()
        assert "fuel_level" in s.errors

    def test_fuel_level_below_0_rejected(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station, fuel_level=-1))
        assert not s.is_valid()
        assert "fuel_level" in s.errors

    def test_fuel_level_boundary_0_accepted(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station, fuel_level=0))
        assert s.is_valid(), s.errors

    def test_fuel_level_boundary_100_accepted(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station, fuel_level=100))
        assert s.is_valid(), s.errors

    def test_negative_odometer_rejected(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station, odometer_km=-1))
        assert not s.is_valid()
        assert "odometer_km" in s.errors

    def test_odometer_zero_accepted(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station, odometer_km=0))
        assert s.is_valid(), s.errors

    def test_year_before_1990_rejected(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station, year=1989))
        assert not s.is_valid()
        assert "year" in s.errors

    def test_year_1990_accepted(self, car_model, station):
        s = CarWriteSerializer(data=self._base(car_model, station, year=1990))
        assert s.is_valid(), s.errors


@pytest.mark.django_db
class TestCarWriteSerializerCreate:

    def test_create_builds_point_from_lon_lat(self, car_model, station):
        s = CarWriteSerializer(data={
            "carModel": car_model.pk,
            "plate": "CREATE01",
            "station": station.pk,
            "status": "AVAILABLE",
            "odometer_km": 0,
            "fuel_level": 50,
            "year": 2021,
            "longitude": 69.24,
            "latitude": 41.30,
        })
        assert s.is_valid(), s.errors
        car = s.save()
        assert car.current_location.x == pytest.approx(69.24)
        assert car.current_location.y == pytest.approx(41.30)
        assert car.current_location.srid == 4326


@pytest.mark.django_db
class TestCarWriteSerializerUpdate:

    def test_update_changes_location_when_provided(self, car):
        s = CarWriteSerializer(car, data={
            "carModel": car.carModel.pk,
            "plate": car.plate,
            "station": car.station.pk,
            "status": car.status,
            "odometer_km": car.odometer_km,
            "fuel_level": car.fuel_level,
            "year": car.year,
            "longitude": 70.0,
            "latitude": 42.0,
        })
        assert s.is_valid(), s.errors
        updated = s.save()
        assert updated.current_location.x == pytest.approx(70.0)
        assert updated.current_location.y == pytest.approx(42.0)

    def test_update_preserves_location_when_not_provided(self, car):
        original_x = car.current_location.x
        s = CarWriteSerializer(car, data={
            "carModel": car.carModel.pk,
            "plate": car.plate,
            "station": car.station.pk,
            "status": car.status,
            "odometer_km": car.odometer_km,
            "fuel_level": car.fuel_level,
            "year": car.year,
        }, partial=True)
        assert s.is_valid(), s.errors
        updated = s.save()
        assert updated.current_location.x == pytest.approx(original_x)
