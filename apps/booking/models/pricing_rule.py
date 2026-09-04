from django.db import models

from django.contrib.postgres.forms import DateTimeRangeField
from apps.enums import PricingRuleType, PricingScope


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


