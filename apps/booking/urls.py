from django.urls import path

from .views import BookingCreateView, BookingDetailView

urlpatterns = [
    path("api/v1/bookings/", BookingCreateView.as_view(), name="booking-create"),
    path("api/v1/bookings/<int:id>/", BookingDetailView.as_view(), name="booking-detail"),
]