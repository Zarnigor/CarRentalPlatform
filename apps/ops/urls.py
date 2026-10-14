from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OpsViewSet, PricingRuleViewSet

router = DefaultRouter()
router.register("", OpsViewSet, basename="ops")
router.register("pricing-rule", PricingRuleViewSet, basename="pricing-rule")
urlpatterns = [path("", include(router.urls))]
