from django.urls import path
from .views import NearbyStationsView

urlpatterns = [
    path('api/v1/stations/nearby/', NearbyStationsView.as_view(), name="stations-nearby"),
]