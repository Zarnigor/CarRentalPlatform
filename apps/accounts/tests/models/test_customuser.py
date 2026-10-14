import pytest

from django.db import IntegrityError

from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestCustomUser:

    def test_creates_user_without_passport_code(self):
        user = CustomUser.objects.create_user(username="alice", password="pw")
        assert user.pk is not None

    def test_inherits_from_abstract_user(self):
        from django.contrib.auth.models import AbstractUser
        assert issubclass(CustomUser, AbstractUser)

    def test_username_is_unique(self):
        CustomUser.objects.create_user(username="dave", password="pw")
        with pytest.raises(IntegrityError):
            CustomUser.objects.create_user(username="dave", password="pw2")
