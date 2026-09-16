from rest_framework.generics import RetrieveAPIView

from .serializers import BookingDetailSerializer
from .models import Booking


class BookingDetailView(RetrieveAPIView):
    serializer_class = BookingDetailSerializer
    queryset = Booking.objects.select_related('customer', 'car', 'station')
    lookup_field = 'id'
