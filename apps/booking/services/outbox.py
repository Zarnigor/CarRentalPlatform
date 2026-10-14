from apps.booking.models import OutboxEvent


def emit(*, aggregate_type: str, aggregate_id: int, event_type: str, payload: dict) -> OutboxEvent:
    return OutboxEvent.objects.create(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
    )
