import uuid
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db import models
from django.db.models import Q
from apps.accounts.models import Customer
from apps.booking.enums import BookingStatus
from apps.fleet.models import Car
from apps.geo.models import Station
from django.contrib.postgres.fields import DateTimeRangeField


class Booking(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    pickup_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="pickup_bookings",)
    dropoff_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="dropoff_bookings",)
    pricing_rule = models.ForeignKey('booking.PricingRule', on_delete=models.PROTECT, null=True, blank=True)
    period = DateTimeRangeField()
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    idempotency_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    hold_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_bookings',
                expressions=[
                    ('car', RangeOperators.EQUAL),
                    ('period', RangeOperators.OVERLAPS),
                ],
                condition=Q(status__in=['pending', 'confirmed']),
            )
        ]