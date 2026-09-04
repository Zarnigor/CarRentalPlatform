import uuid

from django.db import models
from apps.accounts.models import Customer
from apps.enums import BookingStatus
from apps.fleet.models import Car
from apps.geo.models import Station
from django.contrib.postgres.forms import DateTimeRangeField


class Booking(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    pickup_station = models.ForeignKey(Station, on_delete=models.CASCADE)
    dropoff_station = models.ForeignKey(Station, on_delete=models.CASCADE)
    period = DateTimeRangeField()
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    idempotency_key = models.UUIDField(default=uuid.uuid4, editable=False)
    hold_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)