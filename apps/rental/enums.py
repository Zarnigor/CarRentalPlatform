from django.db import models
from django.utils.translation import gettext_lazy as _


class RentalStatus(models.TextChoices):
    ACTIVE = 'active', _('Active')
    COMPLETED = 'completed', _('Completed')
    DISPUTED = 'disputed', _('Disputed')
