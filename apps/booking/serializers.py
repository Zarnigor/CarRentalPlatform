from rest_framework import serializers
from .models import Booking

class BookingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'