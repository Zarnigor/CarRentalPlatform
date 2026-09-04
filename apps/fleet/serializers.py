from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

class AvailabilitySerializer(serializers.Serializer):
    period_from = serializers.DateTimeField(source="from")
    period_to = serializers.DateTimeField(source="to")


class CarAvailabilityQuerySerializer(serializers.Serializer):
    period_from = serializers.DateTimeField()
    period_to = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["period_from"] >= attrs["period_to"]:
            raise serializers.ValidationError(
                _("`to` qiymati `from`dan katta bo'lishi kerak")
            )
        return attrs


class CarAvailabilitySerializer(serializers.Serializer):
    available = serializers.BooleanField()