from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StationViewSet

router = DefaultRouter()
router.register("api/v1/stations", StationViewSet, basename="station")

urlpatterns = [path("", include(router.urls))]
