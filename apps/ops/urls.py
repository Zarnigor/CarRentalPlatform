from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OpsViewSet

router = DefaultRouter()
router.register("api/v1/ops", OpsViewSet, basename="ops")

urlpatterns = [path("", include(router.urls))]
