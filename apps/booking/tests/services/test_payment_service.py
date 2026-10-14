import pytest
from decimal import Decimal

from apps.booking.enums import PaymentKind, PaymentStatus
from apps.booking.exceptions import PaymentCaptureFailedError
from apps.booking.models import Payment
from apps.booking.services.payment import PaymentService


@pytest.mark.django_db
class TestPaymentServiceCreateHold:

    def test_creates_deposit_hold_payment(self, confirmed_booking):
        payment = PaymentService().create_hold(
            booking=confirmed_booking,
            amount=Decimal("600000.00"),
        )
        assert payment.pk is not None
        assert payment.kind == PaymentKind.DEPOSIT_HOLD
        assert payment.status == PaymentStatus.PROCESSING
        assert payment.amount == Decimal("600000.00")

    def test_hold_is_linked_to_booking(self, confirmed_booking):
        payment = PaymentService().create_hold(
            booking=confirmed_booking,
            amount=Decimal("100000.00"),
        )
        assert payment.booking_id == confirmed_booking.pk

    def test_hold_persisted_in_db(self, confirmed_booking):
        payment = PaymentService().create_hold(
            booking=confirmed_booking,
            amount=Decimal("200000.00"),
        )
        assert Payment.objects.filter(pk=payment.pk).exists()


@pytest.mark.django_db
class TestPaymentServiceReleaseHold:

    def _make_hold(self, booking, status=PaymentStatus.PROCESSING):
        return Payment.objects.create(
            booking=booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=booking.total_price,
            status=status,
        )

    def test_sets_hold_to_cancelled(self, confirmed_booking):
        self._make_hold(confirmed_booking)
        payment = PaymentService().release_hold(booking=confirmed_booking)
        assert payment.status == PaymentStatus.CANCELLED

    def test_persists_cancelled_status(self, confirmed_booking):
        hold = self._make_hold(confirmed_booking)
        PaymentService().release_hold(booking=confirmed_booking)
        hold.refresh_from_db()
        assert hold.status == PaymentStatus.CANCELLED

    def test_raises_when_no_hold_exists(self, confirmed_booking):
        with pytest.raises(PaymentCaptureFailedError):
            PaymentService().release_hold(booking=confirmed_booking)

    def test_raises_when_hold_already_cancelled(self, confirmed_booking):
        self._make_hold(confirmed_booking, status=PaymentStatus.CANCELLED)
        with pytest.raises(PaymentCaptureFailedError):
            PaymentService().release_hold(booking=confirmed_booking)

    def test_raises_when_hold_already_completed(self, confirmed_booking):
        self._make_hold(confirmed_booking, status=PaymentStatus.COMPLETED)
        with pytest.raises(PaymentCaptureFailedError):
            PaymentService().release_hold(booking=confirmed_booking)


@pytest.mark.django_db
class TestPaymentServiceCaptureFinalAmount:

    def test_creates_balance_payment(self, confirmed_booking):
        payment = PaymentService().capture_final_amount(
            booking=confirmed_booking,
            final_amount=Decimal("450000.00"),
        )
        assert payment.kind == PaymentKind.BALANCE
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.amount == Decimal("450000.00")

    def test_final_payment_linked_to_booking(self, confirmed_booking):
        payment = PaymentService().capture_final_amount(
            booking=confirmed_booking,
            final_amount=Decimal("300000.00"),
        )
        assert payment.booking_id == confirmed_booking.pk

    def test_final_payment_persisted_in_db(self, confirmed_booking):
        payment = PaymentService().capture_final_amount(
            booking=confirmed_booking,
            final_amount=Decimal("300000.00"),
        )
        assert Payment.objects.filter(pk=payment.pk, kind=PaymentKind.BALANCE).exists()


@pytest.mark.django_db
class TestPaymentServiceCancelHold:

    def test_cancel_hold_sets_hold_to_cancelled(self, confirmed_booking):
        Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=confirmed_booking.total_price,
            status=PaymentStatus.PROCESSING,
        )
        payment = PaymentService().cancel_hold(booking=confirmed_booking)
        assert payment.status == PaymentStatus.CANCELLED

    def test_raises_when_no_hold(self, confirmed_booking):
        with pytest.raises(PaymentCaptureFailedError):
            PaymentService().cancel_hold(booking=confirmed_booking)
