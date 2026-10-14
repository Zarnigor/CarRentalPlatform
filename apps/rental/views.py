import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.rental.models import Rental
from apps.rental.serializers import (
    RentalStartSerializer,
    RentalUpdateSerializer,
    RentalFinishSerializer,
    RentalDetailSerializer,
)
from apps.rental.services import RentalService


class RentalFilter(django_filters.FilterSet):
    booking_id = django_filters.NumberFilter(field_name="booking_id")

    class Meta:
        model = Rental
        fields = ["booking_id", "status"]


class RentalViewSet(ModelViewSet):
    queryset = Rental.objects.select_related("booking")
    lookup_field = "id"
    filter_backends = [DjangoFilterBackend]
    filterset_class = RentalFilter

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST")

    def get_serializer_class(self):
        return {
            "start": RentalStartSerializer,
            "update": RentalUpdateSerializer,
            "partial_update": RentalUpdateSerializer,
            "finish": RentalFinishSerializer,
        }.get(self.action, RentalDetailSerializer)

    @action(detail=False, methods=["post"])
    def start(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        rental = RentalService().start_rental(**s.validated_data)
        return Response(RentalDetailSerializer(rental).data, status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        s = RentalUpdateSerializer(data=request.data, partial=partial)
        s.is_valid(raise_exception=True)
        rental = RentalService().update_rental(rental_id=kwargs["id"], **s.validated_data)
        return Response(RentalDetailSerializer(rental).data)

    @action(detail=True, methods=["post"])
    def finish(self, request, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        rental = RentalService().finish_rental(rental_id=kwargs["id"], **s.validated_data)
        return Response(RentalDetailSerializer(rental).data)