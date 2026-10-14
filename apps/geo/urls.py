from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CityViewSet, StationNearbyViewSet, StationViewSet

router = DefaultRouter()
router.register("station", StationViewSet, basename="station")
router.register("station", StationNearbyViewSet, basename="station_nearby")
router.register("city", CityViewSet, basename="city")

urlpatterns = [path("", include(router.urls))]
