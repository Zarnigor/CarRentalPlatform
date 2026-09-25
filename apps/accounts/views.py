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

from .mixins import ActionPermissionMixin, ActionSerializerMixin
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


class AuthViewSet(ActionSerializerMixin, ActionPermissionMixin, GenericViewSet):
    queryset = CustomUser.objects.none()

    serializer_action_map = {
        "token": CustomTokenObtainPairSerializer,
        "token_refresh": TokenRefreshSerializer,
        "token_verify": TokenVerifySerializer,
        "register": RegisterSerializer,
        "logout": LogoutSerializer,
    }
    default_serializer_class = MeSerializer

    public_actions = {"token", "token_refresh", "token_verify", "register"}

    def _validate_and_respond(self, serializer_class, data):
        s = serializer_class(data=data)
        try:
            s.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])
        return Response(s.validated_data)

    @action(methods=["post"], detail=False, url_path="token")
    def token(self, request):
        return self._validate_and_respond(self.get_serializer_class(), request.data)

    @action(methods=["post"], detail=False, url_path="token/refresh")
    def token_refresh(self, request):
        return self._validate_and_respond(self.get_serializer_class(), request.data)

    @action(methods=["post"], detail=False, url_path="token/verify")
    def token_verify(self, request):
        return self._validate_and_respond(self.get_serializer_class(), request.data)

    @action(methods=["post"], detail=False, url_path="register", permission_classes=[AllowAny])
    def register(self, request):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(AccountService().register(**s.validated_data), status=201)

    @action(methods=["post"], detail=False, url_path="logout")
    def logout(self, request):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        AccountService().logout(refresh_token=s.validated_data["refresh"])
        return Response(status=204)

    @action(methods=["get", "patch"], detail=False, url_path="me")
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
