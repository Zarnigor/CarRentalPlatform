from rest_framework import viewsets

from apps.damage.models import Damage
from apps.damage.serializers import DamageWriteSerializer, DamageReadSerializer


class DamageViewSet(viewsets.ModelViewSet):
    queryset = Damage.objects.select_related("rental").all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DamageWriteSerializer
        return DamageReadSerializer