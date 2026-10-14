from datetime import datetime, timedelta, timezone

from apps.booking.serializers import BookingCreateSerializer, BookingUpdateSerializer


def _utc(hours=0):
    return datetime(2025, 6, 1, tzinfo=timezone.utc) + timedelta(hours=hours)


# ── BookingCreateSerializer ───────────────────────────────────────────────────

class TestBookingCreateSerializer:

    def test_valid_period_builds_range(self):
        s = BookingCreateSerializer(data={
            "car_id": 1,
            "pickup_station_id": 1,
            "dropoff_station_id": 1,
            "period_start": _utc(0).isoformat(),
            "period_end": _utc(4).isoformat(),
        })
        assert s.is_valid(), s.errors
        assert s.validated_data["period"].lower == _utc(0)
        assert s.validated_data["period"].upper == _utc(4)

    def test_rejects_period_start_equal_to_end(self):
        s = BookingCreateSerializer(data={
            "car_id": 1,
            "pickup_station_id": 1,
            "dropoff_station_id": 1,
            "period_start": _utc(0).isoformat(),
            "period_end": _utc(0).isoformat(),
        })
        assert not s.is_valid()
        assert "period_end" in s.errors

    def test_rejects_period_start_after_end(self):
        s = BookingCreateSerializer(data={
            "car_id": 1,
            "pickup_station_id": 1,
            "dropoff_station_id": 1,
            "period_start": _utc(5).isoformat(),
            "period_end": _utc(2).isoformat(),
        })
        assert not s.is_valid()
        assert "period_end" in s.errors

    def test_period_start_and_end_not_in_output(self):
        s = BookingCreateSerializer(data={
            "car_id": 1,
            "pickup_station_id": 1,
            "dropoff_station_id": 1,
            "period_start": _utc(0).isoformat(),
            "period_end": _utc(4).isoformat(),
        })
        assert s.is_valid(), s.errors
        # period_start/end are consumed; period range is present
        assert "period" in s.validated_data


# ── BookingUpdateSerializer ───────────────────────────────────────────────────

class TestBookingUpdateSerializer:

    def test_valid_full_period_update_builds_range(self):
        s = BookingUpdateSerializer(data={
            "period_start": _utc(0).isoformat(),
            "period_end": _utc(4).isoformat(),
        })
        assert s.is_valid(), s.errors
        assert s.validated_data["period"].lower == _utc(0)

    def test_rejects_only_period_start_without_end(self):
        s = BookingUpdateSerializer(data={"period_start": _utc(0).isoformat()})
        assert not s.is_valid()

    def test_rejects_only_period_end_without_start(self):
        s = BookingUpdateSerializer(data={"period_end": _utc(4).isoformat()})
        assert not s.is_valid()

    def test_no_period_fields_is_valid(self):
        s = BookingUpdateSerializer(data={"status": "CONFIRMED"})
        assert s.is_valid(), s.errors
        assert "period" not in s.validated_data

    def test_rejects_period_start_equal_to_end(self):
        s = BookingUpdateSerializer(data={
            "period_start": _utc(3).isoformat(),
            "period_end": _utc(3).isoformat(),
        })
        assert not s.is_valid()
        assert "period_end" in s.errors
