from django.urls import path

from .views import CarAvailabilityView, CarSearchView

urlpatterns = [
    path("cars/<int:car_id>/availability/", CarAvailabilityView.as_view(), name="car-availability"),
    path("cars/search", CarSearchView.as_view(), name="cars-search"),
]