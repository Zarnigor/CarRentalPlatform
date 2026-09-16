from django.db import models
from apps.booking.enums import DamageType, DamageSeverity
from apps.booking.models.rental import Rental


class Damage(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    damage_type = models.CharField(max_length=20, choices=DamageType.choices)
    severity = models.CharField(max_length=20, choices=DamageSeverity.choices)
    location = models.CharField(max_length=20) # damage bo'lgan joy, kapot, fara
    description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    reported_at = models.DateField()
    resolved_at = models.DateTimeField(auto_now_add=True)
