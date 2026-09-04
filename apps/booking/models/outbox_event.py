from django.db import models

class OutboxEvent(models.Model):
    aggregate_type = models.CharField(max_length=200)
    aggregate_id = models.IntegerField()
    event_type = models.CharField(max_length=200)
    payload =models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField()
