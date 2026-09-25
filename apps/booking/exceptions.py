from django.utils.translation import gettext_lazy as _

from root.exceptions import (
    ConflictError,
    NotFoundError,
    PaymentRequiredError,
    ServiceUnavailableError,
    UnprocessableEntityError,
    UpstreamServiceError,
)


class BookingNotFoundError(NotFoundError):
    default_message = _("Booking topilmadi")
    error_code = "booking_not_found"

    def __init__(self, booking_id=None, **extra):
        super().__init__(booking_id=booking_id, **extra)


class BookingNotCancellableError(ConflictError):
    default_message = _("Booking hozirgi holatda bekor qilinmaydi")
    error_code = "booking_not_cancellable"

    def __init__(self, booking_id=None, current_status=None, **extra):
        super().__init__(booking_id=booking_id, current_status=current_status, **extra)


class CarNotAvailableForPeriodError(ConflictError):
    default_message = _("Mashina tanlangan davrda band")
    error_code = "car_not_available_for_period"

    def __init__(self, car_id=None, period=None, **extra):
        super().__init__(car_id=car_id, period=period, **extra)


class PaymentDeclinedError(PaymentRequiredError):
    default_message = _("To'lov rad etildi")
    error_code = "payment_declined"

    def __init__(self, booking_id=None, **extra):
        super().__init__(booking_id=booking_id, **extra)


class PaymentCaptureFailedError(PaymentRequiredError):
    default_message = _("To'lovni yakunlab bo'lmadi, qo'lda tekshirish talab qilinadi")
    error_code = "payment_capture_failed"

    def __init__(self, rental_id=None, **extra):
        super().__init__(rental_id=rental_id, **extra)


class PaymentProviderTimeoutError(UpstreamServiceError):
    default_message = _("To'lov provayderi javob bermadi")
    error_code = "payment_provider_timeout"


class PaymentProviderUnavailableError(ServiceUnavailableError):
    default_message = _("To'lov xizmati vaqtincha ishlamayapti")
    error_code = "payment_provider_unavailable"


class OutboxEventPublishError(UpstreamServiceError):
    default_message = _("Hodisani (event) yuborib bo'lmadi")
    error_code = "outbox_event_publish_failed"


class MissingIdempotencyKeyError(UnprocessableEntityError):
    default_message = _("Idempotency-Key header talab qilinadi")
    error_code = "missing_idempotency_key"
