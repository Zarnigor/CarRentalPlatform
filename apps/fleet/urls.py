from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.fleet.views import CarViewSet
from apps.fleet.views import CarModelViewSet

router = DefaultRouter()
router.register("car", CarViewSet, basename="car")
router.register("car-model", CarModelViewSet, basename="carModel")

urlpatterns = [path("", include(router.urls))]
