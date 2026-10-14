from django.db import models
from apps.accounts.models import CustomUser

class RelocationPlan(models.Model):
    created_by = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    total_driver_km = models.DecimalField(max_digits=10,decimal_places=2)
    algorith_used = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)