from rest_framework import serializers


class UtilizationQuerySerializer(serializers.Serializer):
    date_from = serializers.DateTimeField()
    date_to = serializers.DateTimeField()
    granularity = serializers.ChoiceField(choices=["hour", "day"], default="hour")

    def validate(self, attrs):
        if attrs["date_to"] <= attrs["date_from"]:
            raise serializers.ValidationError("date_to must be after date_from.")
        return attrs


class UtilizationBucketSerializer(serializers.Serializer):
    bucket_start = serializers.DateTimeField(source="bucket_start")
    bucket_end = serializers.DateTimeField(source="bucket_end")
    total_cars = serializers.IntegerField()
    busy_car_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    utilization_pct = serializers.DecimalField(max_digits=5, decimal_places=2)
