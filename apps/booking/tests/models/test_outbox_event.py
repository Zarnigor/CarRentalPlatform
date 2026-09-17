import pytest
from datetime import datetime, timedelta, timezone

from apps.booking.models import OutboxEvent


def _utc(hours: int = 0) -> datetime:
    return datetime(2025, 6, 1, tzinfo=timezone.utc) + timedelta(hours=hours)


@pytest.mark.django_db
class TestOutboxEventModel:

    def test_creates_outbox_event(self):
        event = OutboxEvent.objects.create(
            aggregate_type="Booking",
            aggregate_id=1,
            event_type="booking.confirmed",
            payload={"booking_id": 1, "customer_id": 42},
            published_at=_utc(0),
        )
        assert event.pk is not None

    def test_payload_accepts_nested_json(self):
        event = OutboxEvent.objects.create(
            aggregate_type="Rental",
            aggregate_id=5,
            event_type="rental.started",
            payload={"nested": {"key": "value", "list": [1, 2, 3]}},
            published_at=_utc(0),
        )
        event.refresh_from_db()
        assert event.payload["nested"]["list"] == [1, 2, 3]

    def test_created_at_auto_populated(self):
        event = OutboxEvent.objects.create(
            aggregate_type="Payment",
            aggregate_id=7,
            event_type="payment.captured",
            payload={},
            published_at=_utc(0),
        )
        assert event.created_at is not None

    def test_aggregate_type_max_length(self):
        field = OutboxEvent._meta.get_field("aggregate_type")
        assert field.max_length == 200

    def test_event_type_max_length(self):
        field = OutboxEvent._meta.get_field("event_type")
        assert field.max_length == 200
