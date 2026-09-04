import uuid

from django.db import models
from apps.booking.models.booking import Booking
from apps.enums import PaymentKind, PaymentStatus


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name='payments')
    provider_ref = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    kind = models.CharField(max_length=15, choices=PaymentKind.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=PaymentStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




