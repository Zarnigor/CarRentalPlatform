from django.utils.translation import gettext_lazy as _

class AppError(Exception):
    status_code = 500
    default_message = _("Kutilmagan xatolik yuz berdi")
    error_code = "internal_error"

    def __init__(self, message: str | None = None, **extra):
        self.message = message or self.default_message
        self.extra = extra
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict:
        return {
            "error": self.error_code,
            "message": self.message,
            **self.extra,
        }


class ValidationError(AppError):
    status_code = 400
    default_message = _("So'rov ma'lumotlari noto'g'ri")
    error_code = "validation_error"


class UnauthorizedError(AppError):
    status_code = 401
    default_message = _("Autentifikatsiya talab qilinadi")
    error_code = "unauthorized"


class PaymentRequiredError(AppError):
    status_code = 402
    default_message = _("To'lov talab qilinadi")
    error_code = "payment_required"


class PermissionDeniedError(AppError):
    status_code = 403
    default_message = _("Bu amalni bajarishga ruxsatingiz yo'q")
    error_code = "permission_denied"


class NotFoundError(AppError):
    status_code = 404
    default_message = _("Resurs topilmadi")
    error_code = "not_found"


class ConflictError(AppError):
    status_code = 409
    default_message = _("Resurs joriy holati bilan ziddiyat")
    error_code = "conflict"


class UnprocessableEntityError(AppError):
    status_code = 422
    default_message = _("So'rovni qayta ishlab bo'lmadi")
    error_code = "unprocessable_entity"


class RateLimitedError(AppError):
    status_code = 429
    default_message = _("Juda ko'p so'rov yuborildi, birozdan keyin urinib ko'ring")
    error_code = "rate_limited"


class UpstreamServiceError(AppError):
    status_code = 502
    default_message = _("Tashqi servisda xatolik yuz berdi")
    error_code = "upstream_error"


class ServiceUnavailableError(AppError):
    status_code = 503
    default_message = _("Servis vaqtincha ishlamayapti")
    error_code = "service_unavailable"


