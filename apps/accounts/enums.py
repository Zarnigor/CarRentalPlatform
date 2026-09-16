from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerTier(models.TextChoices):
    STANDARD = "STANDARD", _("standard")
    SILVER = "SILVER", _("silver")
    GOLD = "GOLD", _("gold")
    PLATINUM = "PLATINUM", _("platinum")