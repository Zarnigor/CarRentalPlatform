from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
    TokenVerifySerializer,
)

from .models import Customer, CustomUser
from .serializers import (
    CustomerReadSerializer,
    CustomerUpdateSerializer,
    CustomerWriteSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    MeSerializer,
    RegisterSerializer,
)
from .services import AccountService
from .utils import _me_data


class AuthViewSet(GenericViewSet):
    queryset = CustomUser.objects.none()

    def _validate_and_respond(self, serializer_class, data):
        s = serializer_class(data=data)
        try:
            s.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])
        return Response(s.validated_data)

    @action(methods=["post"], detail=False, url_path="token", permission_classes=[AllowAny], serializer_class=CustomTokenObtainPairSerializer)
    def token(self, request):
        return self._validate_and_respond(self.get_serializer_class(), request.data)

    @action(methods=["post"], detail=False, url_path="token/refresh", permission_classes=[AllowAny], serializer_class=TokenRefreshSerializer)
    def token_refresh(self, request):
        return self._validate_and_respond(self.get_serializer_class(), request.data)

    @action(methods=["post"], detail=False, url_path="token/verify", permission_classes=[AllowAny], serializer_class=TokenVerifySerializer)
    def token_verify(self, request):
        return self._validate_and_respond(self.get_serializer_class(), request.data)

    @action(methods=["post"], detail=False, url_path="register", permission_classes=[AllowAny], serializer_class=RegisterSerializer)
    def register(self, request):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(AccountService().register(**s.validated_data), status=201)

    @action(methods=["post"], detail=False, url_path="logout", serializer_class=LogoutSerializer)
    def logout(self, request):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        AccountService().logout(refresh_token=s.validated_data["refresh"])
        return Response(status=204)

    @action(methods=["get", "patch"], detail=False, url_path="me", serializer_class=MeSerializer)
    def me(self, request):
        if request.method == "PATCH":
            s = self.get_serializer(data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            AccountService().update_me(user=request.user, **s.validated_data)
            request.user.refresh_from_db()
        return Response(MeSerializer(_me_data(request.user)).data)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.select_related("user").all()
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return CustomerWriteSerializer
        if self.action == "partial_update":
            return CustomerUpdateSerializer
        return CustomerReadSerializer
