from django.urls import path

from .views import UtilizationView

urlpatterns = [
    path("api/v1/ops/utilization/", UtilizationView.as_view(), name="ops-utilization"),
]
