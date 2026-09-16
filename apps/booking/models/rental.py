from django.db import models

from apps.booking.enums import RentalStatus


class Rental(models.Model):
    booking = models.ForeignKey('booking.Booking', on_delete=models.CASCADE, related_name="rentals")
    started_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)
    start_odometer = models.DecimalField(max_digits=10, decimal_places=2)
    end_odometer = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=RentalStatus.choices, default=RentalStatus.ACTIVE)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    extra_km_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0)