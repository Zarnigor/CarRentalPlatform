from django.urls import path
from apps.accounts.views import CustomTokenObtainPairView

urlpatterns = [
    path('auth/token/', CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
]