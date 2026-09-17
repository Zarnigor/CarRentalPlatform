import pytest

from apps.booking.enums import BookingStatus
from apps.booking.exceptions import BookingNotCancellableError, BookingNotFoundError
from apps.booking.models import Payment
from apps.booking.services import BookingService


@pytest.mark.django_db
class TestCancelBooking:

    def test_cancels_pending_booking(self, customer, confirmed_booking):
        confirmed_booking.status = BookingStatus.PENDING
        confirmed_booking.save(update_fields=["status"])

        service = BookingService()
        cancelled = service.cancel_booking(booking_id=confirmed_booking.id, customer=customer)

        assert cancelled.status == BookingStatus.CANCELLED

    def test_cancels_confirmed_booking(self, customer, confirmed_booking):
        service = BookingService()
        cancelled = service.cancel_booking(booking_id=confirmed_booking.id, customer=customer)

        assert cancelled.status == BookingStatus.CANCELLED

    def test_releases_payment_hold_on_cancel(self, customer, confirmed_booking):
        from apps.booking.enums import PaymentKind, PaymentStatus

        # Place a hold first so cancel has something to release.
        Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=confirmed_booking.total_price,
            status=PaymentStatus.PROCESSING,
        )

        service = BookingService()
        service.cancel_booking(booking_id=confirmed_booking.id, customer=customer)

        hold = Payment.objects.get(booking=confirmed_booking, kind=PaymentKind.DEPOSIT_HOLD)
        assert hold.status == PaymentStatus.CANCELLED

    def test_raises_when_booking_not_found(self, customer):
        service = BookingService()

        with pytest.raises(BookingNotFoundError):
            service.cancel_booking(booking_id=99999, customer=customer)

    def test_raises_when_booking_is_active(self, customer, confirmed_booking):
        confirmed_booking.status = BookingStatus.ACTIVE
        confirmed_booking.save(update_fields=["status"])

        service = BookingService()
        with pytest.raises(BookingNotCancellableError):
            service.cancel_booking(booking_id=confirmed_booking.id, customer=customer)

    def test_raises_when_booking_is_completed(self, customer, confirmed_booking):
        confirmed_booking.status = BookingStatus.COMPLETED
        confirmed_booking.save(update_fields=["status"])

        service = BookingService()
        with pytest.raises(BookingNotCancellableError):
            service.cancel_booking(booking_id=confirmed_booking.id, customer=customer)
