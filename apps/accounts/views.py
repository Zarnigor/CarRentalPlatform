from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenVerifySerializer
from .models import CustomUser
from .serializers import CustomTokenObtainPairSerializer, LogoutSerializer, MeSerializer, RegisterSerializer
from .services import AccountService
from .utils import _me_data


class AuthViewSet(GenericViewSet):
    queryset = CustomUser.objects.none()
    serializer_class = MeSerializer

    def get_permissions(self):
        public = {"token", "token_refresh", "token_verify", "register"}
        if self.action in public:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(methods=["post"], detail=False, url_path="token", permission_classes=[AllowAny])
    def token(self, request):
        s = CustomTokenObtainPairSerializer(data=request.data)
        try:
            s.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])
        return Response(s.validated_data)

    @action(methods=["post"], detail=False, url_path="token/refresh", permission_classes=[AllowAny])
    def token_refresh(self, request):
        s = TokenRefreshSerializer(data=request.data)
        try:
            s.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])
        return Response(s.validated_data)

    @action(methods=["post"], detail=False, url_path="token/verify", permission_classes=[AllowAny])
    def token_verify(self, request):
        s = TokenVerifySerializer(data=request.data)
        try:
            s.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])
        return Response(s.validated_data)

    @action(methods=["post"], detail=False, url_path="register", permission_classes=[AllowAny])
    def register(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(AccountService().register(**s.validated_data), status=201)

    @action(methods=["post"], detail=False, url_path="logout")
    def logout(self, request):
        s = LogoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        AccountService().logout(refresh_token=s.validated_data["refresh"])
        return Response(status=204)

    @action(methods=["get", "patch"], detail=False, url_path="me")
    def me(self, request):
        if request.method == "PATCH":
            s = MeSerializer(data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            AccountService().update_me(user=request.user, **s.validated_data)
        return Response(MeSerializer(_me_data(request.user)).data)
