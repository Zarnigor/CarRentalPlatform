from decimal import Decimal
from apps.booking.enums import PaymentKind, PaymentStatus
from apps.booking.models import Payment, Booking
from apps.booking.exceptions import PaymentCaptureFailedError


class PaymentService:

    def create_hold(self, *, booking: Booking, amount: Decimal) -> Payment:
        return Payment.objects.create(
            booking=booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=amount,
            status=PaymentStatus.PROCESSING,
        )

    def release_hold(self, *, booking: Booking) -> Payment:
        """
        Hold'ni bo'shatadi (pul band qilingan holatdan chiqadi, capture qilinmaydi).
        """
        # with transaction.atomic(): -> booking ichidan murojat qilinadi bunga atomic kerakmas
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

        return payment

    def capture_final_amount(self, *, booking: Booking, final_amount: Decimal) -> Payment:
        """
        Rental tugagach, yakuniy narxni YANGI Payment sifatida capture qiladi.
        """
        payment = Payment.objects.create(
            booking=booking,
            kind=PaymentKind.BALANCE,
            amount=final_amount,
            status=PaymentStatus.COMPLETED,
        )
        return payment

    def cancel_hold(self, *, booking: Booking) -> Payment:
        """
        Booking bekor qilinganda hold'ni bekor qiladi (release bilan bir xil mantiq).
        """
        return self.release_hold(booking=booking)