import pytest
from datetime import date

from apps.accounts.models import Customer, CustomUser
from apps.accounts.services import AccountService
from root.exceptions import PermissionDeniedError, ValidationError


@pytest.mark.django_db
class TestAccountServiceRegister:

    def test_creates_user_and_customer(self):
        service = AccountService()
        result = service.register(
            username="newuser",
            email="new@test.com",
            password="secret123",
            license_no="DL12345",
            license_verified_at=date(2023, 1, 1),
        )
        assert CustomUser.objects.filter(username="newuser").exists()
        assert Customer.objects.filter(license_no="DL12345").exists()
        assert "access" in result
        assert "refresh" in result

    def test_returns_access_and_refresh_tokens(self):
        service = AccountService()
        result = service.register(
            username="tokenuser",
            email="token@test.com",
            password="secret123",
            license_no="DL99999",
            license_verified_at=date(2023, 1, 1),
        )
        assert isinstance(result["access"], str)
        assert isinstance(result["refresh"], str)
        assert len(result["access"]) > 10

    def test_creates_with_optional_name_fields(self):
        service = AccountService()
        service.register(
            username="nameduser",
            email="named@test.com",
            password="secret123",
            license_no="DL11111",
            license_verified_at=date(2023, 1, 1),
            first_name="Ali",
            last_name="Valiyev",
        )
        user = CustomUser.objects.get(username="nameduser")
        assert user.first_name == "Ali"
        assert user.last_name == "Valiyev"

    def test_user_and_customer_created_atomically(self):
        service = AccountService()
        service.register(
            username="atomicuser",
            email="atomic@test.com",
            password="pass",
            license_no="DL00123",
            license_verified_at=date(2023, 6, 1),
        )
        user = CustomUser.objects.get(username="atomicuser")
        assert Customer.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestAccountServiceLogout:

    def test_blacklists_valid_refresh_token(self):
        service = AccountService()
        result = service.register(
            username="logoutuser",
            email="logout@test.com",
            password="secret",
            license_no="DL55555",
            license_verified_at=date(2023, 1, 1),
        )
        service.logout(refresh_token=result["refresh"])

    def test_raises_validation_error_for_invalid_token(self):
        service = AccountService()
        with pytest.raises(ValidationError):
            service.logout(refresh_token="not-a-valid-token")

    def test_raises_validation_error_for_already_blacklisted_token(self):
        service = AccountService()
        result = service.register(
            username="doublelogout",
            email="dl@test.com",
            password="secret",
            license_no="DL66666",
            license_verified_at=date(2023, 1, 1),
        )
        service.logout(refresh_token=result["refresh"])
        with pytest.raises(ValidationError):
            service.logout(refresh_token=result["refresh"])


@pytest.mark.django_db
class TestAccountServiceGetCustomer:

    def test_returns_customer_for_valid_user(self, django_user, customer):
        service = AccountService()
        result = service.get_customer_for_user(user=django_user)
        assert result.pk == customer.pk

    def test_raises_permission_denied_when_no_customer(self):
        user = CustomUser.objects.create_user(username="nocustomer", password="pw")
        service = AccountService()
        with pytest.raises(PermissionDeniedError):
            service.get_customer_for_user(user=user)


@pytest.mark.django_db
class TestAccountServiceUpdateMe:

    def test_updates_email(self, django_user):
        service = AccountService()
        service.update_me(user=django_user, email="new@email.com")
        django_user.refresh_from_db()
        assert django_user.email == "new@email.com"

    def test_updates_first_and_last_name(self, django_user):
        service = AccountService()
        service.update_me(user=django_user, first_name="Test", last_name="User")
        django_user.refresh_from_db()
        assert django_user.first_name == "Test"
        assert django_user.last_name == "User"

    def test_ignores_unknown_fields(self, django_user):
        original_username = django_user.username
        service = AccountService()
        service.update_me(user=django_user, username="shouldnotchange", email="ok@test.com")
        django_user.refresh_from_db()
        assert django_user.username == original_username

    def test_no_op_when_no_valid_fields(self, django_user):
        original_email = django_user.email
        service = AccountService()
        service.update_me(user=django_user, unknown_field="value")
        django_user.refresh_from_db()
        assert django_user.email == original_email
