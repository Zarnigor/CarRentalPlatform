from django.contrib.gis.db import models


class City(models.Model):
    name = models.CharField(max_length=30)
    timezone = models.CharField(max_length=30)
    boundary = models.MultiPolygonField(srid=4326)


class Station(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    location = models.PointField(srid=4326, geography=True)
    capacity = models.IntegerField()
    geofence = models.PolygonField(srid=4326, geography=True)
    target_count = models.IntegerField()

    #PointField, PolygonField, MultiPolygonField, LineStringField fieldlarda
    #spatial_index default True bo'ladi.
