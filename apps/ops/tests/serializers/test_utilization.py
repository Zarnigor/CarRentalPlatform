from datetime import datetime, timedelta, timezone

from apps.ops.serializers.utilization import UtilizationQuerySerializer


def _utc(hours=0):
    return datetime(2025, 6, 1, tzinfo=timezone.utc) + timedelta(hours=hours)


class TestUtilizationQuerySerializer:

    def test_valid_data_passes(self):
        s = UtilizationQuerySerializer(data={
            "date_from": _utc(0).isoformat(),
            "date_to": _utc(4).isoformat(),
            "granularity": "hour",
        })
        assert s.is_valid(), s.errors

    def test_granularity_defaults_to_hour(self):
        s = UtilizationQuerySerializer(data={
            "date_from": _utc(0).isoformat(),
            "date_to": _utc(4).isoformat(),
        })
        assert s.is_valid(), s.errors
        assert s.validated_data["granularity"] == "hour"

    def test_day_granularity_accepted(self):
        s = UtilizationQuerySerializer(data={
            "date_from": _utc(0).isoformat(),
            "date_to": _utc(48).isoformat(),
            "granularity": "day",
        })
        assert s.is_valid(), s.errors

    def test_invalid_granularity_rejected(self):
        s = UtilizationQuerySerializer(data={
            "date_from": _utc(0).isoformat(),
            "date_to": _utc(4).isoformat(),
            "granularity": "minute",
        })
        assert not s.is_valid()
        assert "granularity" in s.errors

    def test_rejects_date_to_equal_date_from(self):
        s = UtilizationQuerySerializer(data={
            "date_from": _utc(0).isoformat(),
            "date_to": _utc(0).isoformat(),
        })
        assert not s.is_valid()

    def test_rejects_date_to_before_date_from(self):
        s = UtilizationQuerySerializer(data={
            "date_from": _utc(5).isoformat(),
            "date_to": _utc(2).isoformat(),
        })
        assert not s.is_valid()
