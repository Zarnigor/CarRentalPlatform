import uuid
import pytest
from decimal import Decimal
from unittest.mock import patch

from apps.booking.enums import BookingStatus, PaymentKind, PaymentStatus
from apps.booking.exceptions import CarNotAvailableForPeriodError
from apps.booking.models import OutboxEvent, Payment
from apps.booking.services import BookingService
from apps.booking.services.payment import PaymentService
from apps.rental.services import RentalService


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_hold(booking, status=PaymentStatus.PROCESSING):
    return Payment.objects.create(
        booking=booking,
        kind=PaymentKind.DEPOSIT_HOLD,
        amount=booking.total_price,
        status=status,
    )


def _dropoff_inside(station):
    c = station.geofence.centroid
    return c.y, c.x  # lat, lon


# ── BookingService ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookingCreatedEvent:

    def test_emits_booking_created_on_success(self, customer, car, station, booking_period, pricing_rule):
        BookingService().create_booking(
            customer=customer,
            car_id=car.id,
            pickup_station_id=station.id,
            dropoff_station_id=station.id,
            period=booking_period,
            idempotency_key=uuid.uuid4(),
        )
        assert OutboxEvent.objects.filter(
            aggregate_type="booking", event_type="booking.created"
        ).exists()

    def test_booking_created_payload(self, customer, car, station, booking_period, pricing_rule):
        booking, _ = BookingService().create_booking(
            customer=customer,
            car_id=car.id,
            pickup_station_id=station.id,
            dropoff_station_id=station.id,
            period=booking_period,
            idempotency_key=uuid.uuid4(),
        )
        event = OutboxEvent.objects.get(aggregate_type="booking", event_type="booking.created")
        assert event.aggregate_id == booking.id
        assert event.payload["booking_id"] == booking.id
        assert event.payload["customer_id"] == customer.id

    def test_no_event_when_transaction_rolls_back(
        self, customer, car, station, booking_period, pricing_rule
    ):
        # First booking succeeds; second overlaps and raises, rolling back the transaction.
        BookingService().create_booking(
            customer=customer, car_id=car.id,
            pickup_station_id=station.id, dropoff_station_id=station.id,
            period=booking_period, idempotency_key=uuid.uuid4(),
        )
        count_before = OutboxEvent.objects.count()

        with pytest.raises(CarNotAvailableForPeriodError):
            BookingService().create_booking(
                customer=customer, car_id=car.id,
                pickup_station_id=station.id, dropoff_station_id=station.id,
                period=booking_period, idempotency_key=uuid.uuid4(),
            )

        assert OutboxEvent.objects.count() == count_before

    def test_no_event_on_idempotency_replay(self, customer, car, station, booking_period, pricing_rule):
        key = uuid.uuid4()
        BookingService().create_booking(
            customer=customer, car_id=car.id,
            pickup_station_id=station.id, dropoff_station_id=station.id,
            period=booking_period, idempotency_key=key,
        )
        count_after_first = OutboxEvent.objects.filter(event_type="booking.created").count()

        BookingService().create_booking(
            customer=customer, car_id=car.id,
            pickup_station_id=station.id, dropoff_station_id=station.id,
            period=booking_period, idempotency_key=key,
        )
        assert OutboxEvent.objects.filter(event_type="booking.created").count() == count_after_first


@pytest.mark.django_db
class TestBookingCancelledEvent:

    def test_emits_booking_cancelled(self, customer, confirmed_booking):
        _make_hold(confirmed_booking)
        BookingService().cancel_booking(booking_id=confirmed_booking.id, customer=customer)
        assert OutboxEvent.objects.filter(
            aggregate_type="booking",
            aggregate_id=confirmed_booking.id,
            event_type="booking.cancelled",
        ).exists()

    def test_cancelled_event_inside_transaction(self, customer, confirmed_booking):
        _make_hold(confirmed_booking)
        BookingService().cancel_booking(booking_id=confirmed_booking.id, customer=customer)
        event = OutboxEvent.objects.get(event_type="booking.cancelled")
        assert event.payload["booking_id"] == confirmed_booking.id


@pytest.mark.django_db
class TestBookingDeletedEvent:

    def test_emits_booking_deleted(self, confirmed_booking):
        booking_id = confirmed_booking.id
        BookingService().delete_booking(booking_id=booking_id)
        assert OutboxEvent.objects.filter(
            aggregate_type="booking",
            aggregate_id=booking_id,
            event_type="booking.deleted",
        ).exists()


# ── PaymentService ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPaymentHoldCreatedEvent:

    def test_emits_hold_created(self, confirmed_booking):
        PaymentService().create_hold(booking=confirmed_booking, amount=Decimal("600000.00"))
        assert OutboxEvent.objects.filter(
            aggregate_type="payment", event_type="payment.hold_created"
        ).exists()

    def test_hold_created_payload(self, confirmed_booking):
        payment = PaymentService().create_hold(booking=confirmed_booking, amount=Decimal("300000.00"))
        event = OutboxEvent.objects.get(event_type="payment.hold_created")
        assert event.aggregate_id == payment.id
        assert event.payload["booking_id"] == confirmed_booking.id
        assert event.payload["amount"] == "300000.00"


@pytest.mark.django_db
class TestPaymentHoldReleasedEvent:

    def test_emits_hold_released(self, confirmed_booking):
        _make_hold(confirmed_booking)
        PaymentService().release_hold(booking=confirmed_booking)
        assert OutboxEvent.objects.filter(
            aggregate_type="payment", event_type="payment.hold_released"
        ).exists()


@pytest.mark.django_db
class TestPaymentHoldCancelledEvent:

    def test_emits_hold_cancelled(self, confirmed_booking):
        _make_hold(confirmed_booking)
        PaymentService().cancel_hold(booking=confirmed_booking)
        assert OutboxEvent.objects.filter(
            aggregate_type="payment", event_type="payment.hold_cancelled"
        ).exists()

    def test_hold_cancelled_not_hold_released(self, confirmed_booking):
        _make_hold(confirmed_booking)
        PaymentService().cancel_hold(booking=confirmed_booking)
        assert not OutboxEvent.objects.filter(event_type="payment.hold_released").exists()


@pytest.mark.django_db
class TestPaymentCapturedEvent:

    def test_emits_payment_captured(self, confirmed_booking):
        PaymentService().capture_final_amount(booking=confirmed_booking, final_amount=Decimal("450000.00"))
        assert OutboxEvent.objects.filter(
            aggregate_type="payment", event_type="payment.captured"
        ).exists()

    def test_captured_payload(self, confirmed_booking):
        payment = PaymentService().capture_final_amount(
            booking=confirmed_booking, final_amount=Decimal("450000.00")
        )
        event = OutboxEvent.objects.get(event_type="payment.captured")
        assert event.aggregate_id == payment.id
        assert event.payload["amount"] == "450000.00"


# ── RentalService ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRentalStartedEvent:

    def test_emits_rental_started(self, confirmed_booking):
        rental = RentalService().start_rental(
            booking_id=confirmed_booking.id, start_odometer=Decimal("10000.00")
        )
        assert OutboxEvent.objects.filter(
            aggregate_type="rental",
            aggregate_id=rental.id,
            event_type="rental.started",
        ).exists()

    def test_rental_started_payload(self, confirmed_booking):
        rental = RentalService().start_rental(
            booking_id=confirmed_booking.id, start_odometer=Decimal("10000.00")
        )
        event = OutboxEvent.objects.get(event_type="rental.started")
        assert event.payload["booking_id"] == confirmed_booking.id
        assert event.payload["start_odometer"] == "10000.00"


@pytest.mark.django_db
class TestRentalFinishedEvent:

    def test_emits_rental_finished(self, active_rental):
        booking = active_rental.booking
        lat, lon = _dropoff_inside(booking.dropoff_station)
        RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10100.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )
        assert OutboxEvent.objects.filter(
            aggregate_type="rental",
            aggregate_id=active_rental.id,
            event_type="rental.finished",
        ).exists()

    def test_rental_finished_payload_contains_final_price(self, active_rental):
        booking = active_rental.booking
        lat, lon = _dropoff_inside(booking.dropoff_station)
        RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10100.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )
        event = OutboxEvent.objects.get(event_type="rental.finished")
        assert "final_price" in event.payload
        assert event.payload["booking_id"] == booking.id
