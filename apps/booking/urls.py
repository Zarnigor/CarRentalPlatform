from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookingViewSet

router = DefaultRouter()
router.register("api/v1/bookings", BookingViewSet, basename="booking")

urlpatterns = [path("", include(router.urls))]
