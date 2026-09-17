from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import get_utilization
from .serializers import UtilizationBucketSerializer, UtilizationQuerySerializer


class UtilizationView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        query = UtilizationQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        d = query.validated_data
        buckets = get_utilization(
            date_from=d["date_from"],
            date_to=d["date_to"],
            granularity=d["granularity"],
        )
        return Response(UtilizationBucketSerializer(buckets, many=True).data)
