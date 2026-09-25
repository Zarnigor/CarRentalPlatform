from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.rental.views import RentalViewSet

router = DefaultRouter()
router.register("", RentalViewSet, basename="rental")

urlpatterns = [path("", include(router.urls))]
