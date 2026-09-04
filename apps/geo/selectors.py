"""
find_nearby_stations(lat=41.311, lon=69.279, limit=5)
"""
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

from .models import Station


def find_nearby_stations(lat: float, lon: float, limit: int = 10):
    user_location = Point(lon, lat, srid=4326)

    return (
        Station.objects.select_related("city")
        .annotate(distance_m=Distance("location", user_location))
        .order_by("distance_m")[:limit]
    )