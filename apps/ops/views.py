from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .selectors import get_utilization
from .serializers import UtilizationBucketSerializer, UtilizationQuerySerializer


class OpsViewSet(GenericViewSet):
    """GET  api/v1/ops/utilization/"""

    serializer_class = UtilizationBucketSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["get"], url_path="utilization", permission_classes=[IsAdminUser])
    def utilization(self, request):
        query = UtilizationQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        d = query.validated_data
        buckets = get_utilization(
            date_from=d["date_from"],
            date_to=d["date_to"],
            granularity=d["granularity"],
        )
        return Response(UtilizationBucketSerializer(buckets, many=True).data)
