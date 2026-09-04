from django.contrib.gis.db import models


class City(models.Model):
    name = models.CharField(max_length=30)
    timezone = models.CharField(max_length=30)
    boundary = models.MultiPolygonField(srid=4326)


class Station(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    location = models.PointField(srid=4326)
    capacity = models.IntegerField()
    geofence = models.PolygonField(srid=4326)
    target_count = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['location'], name='location'),
        ]

