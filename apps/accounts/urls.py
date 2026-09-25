from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, CustomerViewSet

router = DefaultRouter()
router.register("auth", AuthViewSet, basename="auth")
router.register("customers", CustomerViewSet, basename="customer")

urlpatterns = [path("", include(router.urls))]
