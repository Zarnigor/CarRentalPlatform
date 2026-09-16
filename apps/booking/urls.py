from django.urls import path
from .views import BookingDetailView

urlpatterns = [
    path('bookings/<int:id>/', BookingDetailView.as_view(), name='booking-detail'),
]