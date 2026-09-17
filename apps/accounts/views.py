from django.db import transaction
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Customer, CustomUser
from .serializers import (
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    MeSerializer,
    RegisterSerializer,
)


def _customer_for(user) -> Customer | None:
    return Customer.objects.filter(user_id=user.pk).first()


def _me_data(user) -> dict:
    c = _customer_for(user)
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "license_no": c.license_no if c else None,
        "tier": c.tier if c else None,
        "risk_score": c.risk_score if c else None,
    }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=d["username"],
                email=d["email"],
                password=d["password"],
            )
            Customer.objects.create(
                user=user,
                license_no=d["license_no"],
                license_verified_at=d["license_verified_at"],
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)},
            status=201,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = LogoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            RefreshToken(s.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Token is invalid or already blacklisted."}, status=400)
        return Response(status=204)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(_me_data(request.user)).data)

    def patch(self, request):
        allowed = {"email", "first_name", "last_name"}
        updates = {k: v for k, v in request.data.items() if k in allowed}
        if updates:
            for field, value in updates.items():
                setattr(request.user, field, value)
            request.user.save(update_fields=list(updates))
        return Response(MeSerializer(_me_data(request.user)).data)
