from root.exceptions import NotFoundError, UnauthorizedError, ConflictError, PermissionDeniedError
from django.utils.translation import gettext_lazy as _

class UserNotFoundError(NotFoundError):
    default_message = _("Foydalanuvchi topilmadi")
    error_code = "user_not_found"

    def __init__(self, user_id=None, **extra):
        super().__init__(user_id=user_id, **extra)


class CustomerProfileNotFoundError(NotFoundError):
    default_message = _("Mijoz profili topilmadi")
    error_code = "customer_profile_not_found"

    def __init__(self, user_id=None, **extra):
        super().__init__(user_id=user_id, **extra)


class InvalidCredentialsError(UnauthorizedError):
    default_message = _("Login yoki parol noto'g'ri")
    error_code = "invalid_credentials"


class TokenExpiredError(UnauthorizedError):
    default_message = _("Token muddati tugagan")
    error_code = "token_expired"


class DuplicateEmailError(ConflictError):
    default_message = _("Bu email bilan foydalanuvchi allaqachon mavjud")
    error_code = "duplicate_email"

    def __init__(self, email=None, **extra):
        super().__init__(email=email, **extra)


class ProfileIncompleteError(PermissionDeniedError):
    default_message = _("Profilni to'liq to'ldiring (hujjatlar yetishmayapti)")
    error_code = "profile_incomplete"
