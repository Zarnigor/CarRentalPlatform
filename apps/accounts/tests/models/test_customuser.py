import pytest

from django.db import IntegrityError

from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestCustomUser:

    def test_creates_user_without_passport_code(self):
        user = CustomUser.objects.create_user(username="alice", password="pw")
        assert user.pk is not None
        assert user.passport_code is None

    def test_creates_user_with_passport_code(self):
        user = CustomUser.objects.create_user(
            username="bob", password="pw", passport_code="AB1234567"
        )
        user.refresh_from_db()
        assert user.passport_code == "AB1234567"

    def test_passport_code_is_optional(self):
        user = CustomUser.objects.create_user(username="carol", password="pw")
        assert user.passport_code is None

    def test_passport_code_max_length(self):
        field = CustomUser._meta.get_field("passport_code")
        assert field.max_length == 20

    def test_inherits_from_auth_user(self):
        from django.contrib.auth.models import User
        assert issubclass(CustomUser, User)

    def test_username_is_unique(self):
        CustomUser.objects.create_user(username="dave", password="pw")
        with pytest.raises(IntegrityError):
            CustomUser.objects.create_user(username="dave", password="pw2")
