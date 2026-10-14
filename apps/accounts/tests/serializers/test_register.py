import pytest
from datetime import date
from unittest.mock import MagicMock

from apps.accounts.models import CustomUser
from apps.accounts.serializers import RegisterSerializer, MeSerializer

class TestRegisterSerializerValidateUsername:

    @pytest.mark.django_db
    def test_rejects_existing_username(self):
        CustomUser.objects.create_user(username="taken", password="pw")
        s = RegisterSerializer(data={
            "username": "taken", "email": "x@x.com",
            "password": "StrongPass1!", "password2": "StrongPass1!",
            "license_no": "DL1", "license_verified_at": "2023-01-01",
        })
        assert not s.is_valid()
        assert "username" in s.errors

    @pytest.mark.django_db
    def test_accepts_new_username(self):
        s = RegisterSerializer(data={
            "username": "brandnew", "email": "n@n.com",
            "password": "StrongPass1!", "password2": "StrongPass1!",
            "license_no": "DL2", "license_verified_at": "2023-01-01",
        })
        assert s.is_valid(), s.errors


@pytest.mark.django_db
class TestRegisterSerializerValidate:

    def test_rejects_mismatched_passwords(self):
        s = RegisterSerializer(data={
            "username": "user1", "email": "u@u.com",
            "password": "StrongPass1!", "password2": "Different1!",
            "license_no": "DL3", "license_verified_at": "2023-01-01",
        })
        assert not s.is_valid()
        assert "password2" in s.errors

    def test_rejects_weak_password(self):
        s = RegisterSerializer(data={
            "username": "user2", "email": "u@u.com",
            "password": "123", "password2": "123",
            "license_no": "DL4", "license_verified_at": "2023-01-01",
        })
        assert not s.is_valid()
        assert "password" in s.errors

    def test_valid_data_produces_no_password2_in_output(self):
        s = RegisterSerializer(data={
            "username": "user3", "email": "u@u.com",
            "password": "StrongPass1!", "password2": "StrongPass1!",
            "license_no": "DL5", "license_verified_at": "2023-01-01",
        })
        assert s.is_valid(), s.errors
        assert "password2" not in s.validated_data

    def test_optional_first_last_name_default_empty(self):
        s = RegisterSerializer(data={
            "username": "user4", "email": "u@u.com",
            "password": "StrongPass1!", "password2": "StrongPass1!",
            "license_no": "DL6", "license_verified_at": "2023-01-01",
        })
        assert s.is_valid(), s.errors
        assert s.validated_data["first_name"] == ""
        assert s.validated_data["last_name"] == ""


class TestMeSerializerValidateEmail:

    @pytest.mark.django_db
    def test_rejects_email_used_by_another_user(self):
        CustomUser.objects.create_user(username="other", password="pw", email="used@test.com")
        current_user = CustomUser.objects.create_user(username="me", password="pw", email="me@test.com")
        request = MagicMock()
        request.user = current_user
        s = MeSerializer(
            data={"email": "used@test.com", "first_name": "", "last_name": ""},
            context={"request": request},
        )
        assert not s.is_valid()
        assert "email" in s.errors

    @pytest.mark.django_db
    def test_accepts_own_current_email(self):
        user = CustomUser.objects.create_user(username="me2", password="pw", email="mine@test.com")
        request = MagicMock()
        request.user = user
        s = MeSerializer(
            data={"email": "mine@test.com", "first_name": "", "last_name": ""},
            context={"request": request},
        )
        assert s.is_valid(), s.errors

    @pytest.mark.django_db
    def test_accepts_new_email(self):
        user = CustomUser.objects.create_user(username="me3", password="pw", email="old@test.com")
        request = MagicMock()
        request.user = user
        s = MeSerializer(
            data={"email": "new@test.com", "first_name": "", "last_name": ""},
            context={"request": request},
        )
        assert s.is_valid(), s.errors
