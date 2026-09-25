from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
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


class RentalViewSet(ModelViewSet):
    """
    list          GET    /api/v1/rentals/             — list (filter: ?booking_id=, ?status=)
    create        POST   /api/v1/rentals/             — start rental
    retrieve      GET    /api/v1/rentals/{id}/        — detail
    update        PUT    /api/v1/rentals/{id}/        — full update
    partial_update PATCH /api/v1/rentals/{id}/        — partial update
    destroy       DELETE /api/v1/rentals/{id}/        — delete
    finish        POST   /api/v1/rentals/{id}/finish/ — finish rental
    """

    queryset = Rental.objects.select_related("booking")
    serializer_class = RentalDetailSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return RentalStartSerializer
        if self.action in ("update", "partial_update"):
            return RentalUpdateSerializer
        if self.action == "finish":
            return RentalFinishSerializer
        return RentalDetailSerializer

    def list(self, request, *args, **kwargs):
        booking_id = request.query_params.get("booking_id")
        status = request.query_params.get("status")
        rentals = RentalService().list_rentals(
            booking_id=int(booking_id) if booking_id else None,
            status=status or None,
        )
        return Response(RentalDetailSerializer(rentals, many=True).data)

    def create(self, request, *args, **kwargs):
        s = RentalStartSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        rental = RentalService().start_rental(**s.validated_data)
        return Response(RentalDetailSerializer(rental).data, status=201)

    def retrieve(self, request, *args, **kwargs):
        rental = RentalService().get_rental(rental_id=kwargs["id"])
        return Response(RentalDetailSerializer(rental).data)

    def update(self, request, *args, **kwargs):
        s = RentalUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        rental = RentalService().update_rental(rental_id=kwargs["id"], **s.validated_data)
        return Response(RentalDetailSerializer(rental).data)

    def partial_update(self, request, *args, **kwargs):
        s = RentalUpdateSerializer(data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        rental = RentalService().update_rental(rental_id=kwargs["id"], **s.validated_data)
        return Response(RentalDetailSerializer(rental).data)

    def destroy(self, request, *args, **kwargs):
        RentalService().delete_rental(rental_id=kwargs["id"])
        return Response(status=204)

    @action(detail=True, methods=["post"], url_path="finish")
    def finish(self, request, **kwargs):
        s = RentalFinishSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        rental = RentalService().finish_rental(rental_id=kwargs["id"], **s.validated_data)
        return Response(RentalDetailSerializer(rental).data)
