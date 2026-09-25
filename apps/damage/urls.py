from rest_framework.routers import DefaultRouter
from apps.damage.views import DamageViewSet

router = DefaultRouter()
router.register("", DamageViewSet, basename="damage")

urlpatterns = router.urls