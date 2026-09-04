from django.db import models
from apps.booking.models.booking import Booking


class Rental(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    started_at = models.DateField()
    ended_at = models.DateField()
    start_odometer = models.DecimalField(max_digits=10, decimal_places=2)
    end_odometer = models.DecimalField(max_digits=10, decimal_places=2)
