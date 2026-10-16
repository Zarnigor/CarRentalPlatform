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


class RentalFinishThrottle(UserRateThrottle):
    """3 finish calls per minute per authenticated user — prevents duplicate payment captures."""
    scope = "rental_finish"


class CarAvailabilityThrottle(AnonRateThrottle):
    """30 checks per minute per IP — prevents bulk calendar scraping across car IDs."""
    scope = "car_availability"


class StationsNearbyThrottle(AnonRateThrottle):
    """20 lookups per minute per IP — protects PostGIS KNN query from coordinate flooding."""
    scope = "stations_nearby"
