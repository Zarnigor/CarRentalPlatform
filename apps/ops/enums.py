from django.db import models
from django.utils.translation import gettext_lazy as _

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

