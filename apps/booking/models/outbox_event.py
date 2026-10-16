from django.db import models
from django.db.models import Q


class OutboxEvent(models.Model):
    aggregate_type = models.CharField(max_length=200)
    aggregate_id = models.IntegerField()
    event_type = models.CharField(max_length=200)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        indexes = [
            models.Index(
                fields=["created_at"],
                name="outbox_unpublished_created_idx",
                condition=Q(published_at__isnull=True),
            ),
        ]
