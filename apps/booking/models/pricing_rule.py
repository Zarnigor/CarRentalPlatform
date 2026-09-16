from django.db import models

from django.contrib.postgres.fields import DateTimeRangeField

from apps.booking.enums import PricingScope, PricingRuleType


class PricingRule(models.Model):
    name = models.CharField(max_length=255)
    scope = models.CharField(max_length=30, choices=PricingScope)
    rule_type = models.CharField(max_length=20, choices=PricingRuleType)
    priority = models.PositiveIntegerField(default=0)
    valid_period = DateTimeRangeField()
    multiplier = models.PositiveIntegerField(default=1)
    flat_fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    free_km_per_day = models.PositiveIntegerField(default=0)  # kuniga necha km "bepul"
    price_per_extra_km = models.DecimalField(max_digits=10, decimal_places=2)