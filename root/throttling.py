from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthLoginThrottle(AnonRateThrottle):
    """5 attempts per minute per IP — brute-force protection for /auth/token."""
    scope = "auth_login"


class AuthRegisterThrottle(AnonRateThrottle):
    """3 registrations per minute per IP — prevents account-farming."""
    scope = "auth_register"


class BookingCreateThrottle(UserRateThrottle):
    """5 bookings per minute per authenticated user — guards the payment provider."""
    scope = "booking_create"


class BookingCancelThrottle(UserRateThrottle):
    """10 cancellations per minute per authenticated user — prevents cancel-rebook abuse."""
    scope = "booking_cancel"
