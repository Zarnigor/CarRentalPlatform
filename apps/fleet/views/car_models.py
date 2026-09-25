from rest_framework import viewsets

from apps.fleet.models import CarModel
from apps.fleet.serializers import CarModelWriteSerializer, CarModelReadSerializer


class CarModelViewSet(viewsets.ModelViewSet):
    queryset = CarModel.objects.all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CarModelWriteSerializer
        return CarModelReadSerializer