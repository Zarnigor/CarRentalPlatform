from django.contrib.auth.models import User
from django.db import models

from apps.accounts.enums import CustomerTier


class CustomUser(User):
    passport_code = models.CharField(max_length=20, blank=True, null=True)


class Customer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    license_no = models.CharField(max_length=20)
    license_verified_at = models.DateField()
    risk_score = models.FloatField(default=0)
    tier = models.CharField(
        max_length=20, choices=CustomerTier.choices, default=CustomerTier.STANDARD
    )
