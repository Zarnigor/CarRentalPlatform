from django.urls import path
from .views import NearbyStationsView

urlpatterns = [
    path('stations/nearby/', NearbyStationsView.as_view(), name="stations-nearby"),
]