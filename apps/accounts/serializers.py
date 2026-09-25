from types import SimpleNamespace

from django.contrib.auth.password_validation import (
    validate_password as django_validate_password,
)
from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Customer, CustomUser


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = "staff" if user.is_staff else "customer"
        return token


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    license_no = serializers.CharField(max_length=20)
    license_verified_at = serializers.DateField()

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        class _NoMeta:
            @staticmethod
            def get_field(_):
                raise FieldDoesNotExist

        pseudo_user = SimpleNamespace(
            username=attrs["username"],
            email=attrs["email"],
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            _meta=_NoMeta(),
        )
        try:
            django_validate_password(attrs["password"], user=pseudo_user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        return attrs


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    license_no = serializers.CharField(read_only=True, default=None)
    tier = serializers.CharField(read_only=True, default=None)
    risk_score = serializers.FloatField(read_only=True, default=None)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class CustomerReadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "username",
            "email",
            "license_no",
            "license_verified_at",
            "tier",
            "risk_score",
        ]


class CustomerWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["user", "license_no", "license_verified_at", "tier"]


class CustomerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["license_no", "license_verified_at", "tier"]
