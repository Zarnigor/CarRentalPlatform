from django.db import models
from django.utils.translation import gettext_lazy as _


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
