from django.urls import path

from .views import CarAvailabilityView

urlpatterns = [
    path("cars/<int:car_id>/availability/", CarAvailabilityView.as_view(), name="car-availability"),
]