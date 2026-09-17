from django.db import models

from apps.accounts.models import CustomUser
from apps.fleet.models import Car
from apps.geo.models import Station


class RelocationPlan(models.Model):
    created_by = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    total_driver_km = models.DecimalField(max_digits=10,decimal_places=2)
    algorith_used = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class RelocationTask(models.Model):
    plan = models.ForeignKey(RelocationPlan,on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="relocation_tasks")
    source_station = models.ForeignKey(Station,on_delete=models.CASCADE, related_name="relocation_tasks_from")
    destination_station = models.ForeignKey(Station,on_delete=models.CASCADE, related_name="relocation_tasks_to")
    distance_km = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(max_length=200)
    assigned_to = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="assigned_relocation_tasks")
    completed_at = models.DateTimeField(auto_now_add=True)



