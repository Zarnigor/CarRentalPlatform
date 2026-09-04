from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerTier(models.TextChoices):
    STANDARD = "STANDARD", _("standard")
    SILVER = "SILVER", _("silver")
    GOLD = "GOLD", _("gold")
    PLATINUM = "PLATINUM", _("platinum")


class CarStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", _("available")
    RESERVER = "RESERVER", _("reserver")
    IN_USE = "IN_USE", _("in use")
    MAINTENANCE = "MAINTENANCE", _("maintenance")
    CLEANING = "CLEANING", _("cleaning")
    INSPECTION = "INSPECTION", _("inspection")
    IN_TRANSIT = "IN_TRANSIT", _("in transit")
    BLOCKED = "BLOCKED", _("blocked")
    ACCIDENT = "ACCIDENT", _("accident")
    RETIRED = "RETIRED", _("retired")


class FuelType(models.TextChoices):
    PETROL = "PETROL", _("petrol")
    DIESEL = "DIESEL", _("diesel")
    ELECTRIC = "ELECTRIC", _("electric")
    HYBRID = "HYBRID", _("hybrid")
    GAS = "GAS", _("gas")


class TransmissionType(models.TextChoices):
    MANUAL = "MANUAL", _("manual")
    AUTOMATIC = "AUTOMATIC", _("automatic")
    SEMI_AUTO = "SEMI_AUTOMATIC", _("semi_automatic")
    CTV = "CTV", _("ctv")


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", _("pending")
    CONFIRMED = "CONFIRMED", _("confirmed")
    ACTIVE = "ACTIVE", _("active")
    COMPLETED = "COMPLETED", _("completed")
    CANCELED = "CANCELED", _("canceled")
    EXPIRED = "EXPIRED", _("expired")
    PAYMENT_PENDING = "PAYMENT_PENDING", _("payment_pending")
    PAYMENT_FAILED = "PAYMENT_FAILED", _("payment_failed")


class DamageType(models.TextChoices):
    SCRATCH = "SCRATCH", _("scratch")
    DENT = "DENT", _("dent")
    CRACK = "CRACK", _("crack")
    BROKEN = "BROKEN", _("broken")
    STAINED = "STAINED", _("stained")
    MISSING_PART = "MISSING_PART", _("missing_part")
    MECHANICAL = "MECHANICAL", _("mechanical")


class DamageSeverity(models.TextChoices):
    MINOR = "MINOR", _("minor")
    MODERATE = "MODERATE", _("moderate")
    SEVERE = "SEVERE", _("severe")


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


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", _("pending")
    PROCESSING = "PROCESSING", _("processing")
    COMPLETED = "COMPLETED", _("completed")
    FAILED = "FAILED", _("failed")
    CANCELED = "CANCELED", _("canceled")
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