from django.db import models
from django.utils.translation import gettext_lazy as _


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