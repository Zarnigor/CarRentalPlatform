from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", _("pending")
    PROCESSING = "PROCESSING", _("processing")
    COMPLETED = "COMPLETED", _("completed")
    FAILED = "FAILED", _("failed")
    CANCELLED = "CANCELLED", _("cancelled")
    REFUNDED = "REFUNDED", _("refunded")
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", _("partially_refunded")
    EXPIRED = "EXPIRED", _("expired")


class PaymentKind(models.TextChoices):
    DEPOSIT = "DEPOSIT", _("deposit")
    BALANCE = "BALANCE", _("balance")
    DEPOSIT_HOLD = "DEPOSIT_HOLD", _("deposit_hold")
    PENALTY = "PENALTY", _("penalty")
    REFUND = "REFUND", _("refund")
    EXTRA_LARGE = "EXTRA_LARGE", _("extra_large")


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", _("pending")
    CONFIRMED = "CONFIRMED", _("confirmed")
    ACTIVE = "ACTIVE", _("active")
    COMPLETED = "COMPLETED", _("completed")
    CANCELLED = "CANCELLED", _("cancelled")
    EXPIRED = "EXPIRED", _("expired")
    PAYMENT_PENDING = "PAYMENT_PENDING", _("payment_pending")
    PAYMENT_FAILED = "PAYMENT_FAILED", _("payment_failed")


class PricingScope(models.TextChoices):
    GLOBAL = "GLOBAL", _("global")
    CITY = "CITY", _("city")
    STATION = "STATION", _("station")
    VEHICLE_TYPE = "VEHICLE_TYPE", _("vehicle_type")
    VEHICLE = "VEHICLE", _("vehicle")


class PricingRuleType(models.TextChoices):
    SEASONAL = "SEASONAL", _("seasonal")
    WEEKEND = "WEEKEND", _("weekend")
    HOLIDAY = "HOLIDAY", _("holiday")
    DEMAND_SURGE = "DEMAND_SURGE", _("demand_surge")
    EARLY_BIRD = "EARLY_BIRD", _("early_bird")
    LONG_TERM = "LONG_TERM", _("long_term")

