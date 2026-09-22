from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from .models import Station

# Algo A4 — Nearest stations using ST_DWithin prefilter + KNN ORDER BY <->
# ST_DWithin(location, point, radius) uses the GiST index to discard distant
# rows cheaply; ORDER BY ST_Distance then triggers the KNN index scan for the
# final sort. Without the DWithin prefilter, a large table forces a full-index
# scan for every query.
_DEFAULT_SEARCH_RADIUS_M = 50_000  # 50 km — wide enough for any city


def find_nearby_stations(lat: float, lon: float, limit: int = 10):
    point = Point(lon, lat, srid=4326)
    return (
        Station.objects.select_related("city")
        .filter(location__distance_lte=(point, D(m=_DEFAULT_SEARCH_RADIUS_M)))
        .annotate(distance=Distance("location", point))
        .order_by("distance")[:limit]
    )