from decimal import Decimal
from apps.booking.enums import PaymentKind, PaymentStatus
from apps.booking.models import Payment, Booking
from apps.booking.exceptions import PaymentCaptureFailedError
from apps.booking.services.outbox import emit


class PaymentService:

    def create_hold(self, *, booking: Booking, amount: Decimal) -> Payment:
        payment = Payment.objects.create(
            booking=booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=amount,
            status=PaymentStatus.PROCESSING,
        )
        emit(
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type="payment.hold_created",
            payload={"payment_id": payment.id, "booking_id": booking.id, "amount": str(amount)},
        )
        return payment

    def release_hold(self, *, booking: Booking) -> Payment:
        try:
            payment = Payment.objects.select_for_update().get(
                booking=booking,
                kind=PaymentKind.DEPOSIT_HOLD,
            )
        except Payment.DoesNotExist:
            raise PaymentCaptureFailedError(rental_id=None)

        if payment.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            raise PaymentCaptureFailedError(rental_id=None)

        payment.status = PaymentStatus.CANCELLED
        payment.save(update_fields=["status", "updated_at"])

        emit(
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type="payment.hold_released",
            payload={"payment_id": payment.id, "booking_id": booking.id},
        )
        return payment

    def capture_final_amount(self, *, booking: Booking, final_amount: Decimal) -> Payment:
        payment = Payment.objects.create(
            booking=booking,
            kind=PaymentKind.BALANCE,
            amount=final_amount,
            status=PaymentStatus.COMPLETED,
        )
        emit(
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type="payment.captured",
            payload={"payment_id": payment.id, "booking_id": booking.id, "amount": str(final_amount)},
        )
        return payment

    def cancel_hold(self, *, booking: Booking) -> Payment:
        try:
            payment = Payment.objects.select_for_update().get(
                booking=booking,
                kind=PaymentKind.DEPOSIT_HOLD,
            )
        except Payment.DoesNotExist:
            raise PaymentCaptureFailedError(rental_id=None)

        if payment.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            raise PaymentCaptureFailedError(rental_id=None)

        payment.status = PaymentStatus.CANCELLED
        payment.save(update_fields=["status", "updated_at"])

        emit(
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type="payment.hold_cancelled",
            payload={"payment_id": payment.id, "booking_id": booking.id},
        )
        return payment