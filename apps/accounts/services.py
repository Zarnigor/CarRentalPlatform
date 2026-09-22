from django.db import transaction
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from root.exceptions import PermissionDeniedError, ValidationError
from .models import Customer, CustomUser


class AccountService:
    def register(self, *, username: str, email: str, password: str, license_no: str, license_verified_at) -> dict:
        """Create a new user + customer profile and return JWT tokens.

        Returns:
            Dict with 'access' and 'refresh' token strings.
        """
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            Customer.objects.create(
                user=user,
                license_no=license_no,
                license_verified_at=license_verified_at,
            )

        refresh = RefreshToken.for_user(user)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}

    def logout(self, *, refresh_token: str) -> None:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError as exc:
            raise ValidationError(str(exc))

    def get_customer_for_user(self, *, user) -> Customer:
        try:
            return Customer.objects.get(user_id=user.pk)
        except Customer.DoesNotExist:
            raise PermissionDeniedError()

    def update_me(self, *, user, **fields) -> None:
        _UPDATABLE = {"email", "first_name", "last_name"}
        updates = {k: v for k, v in fields.items() if k in _UPDATABLE}
        if updates:
            for field, value in updates.items():
                setattr(user, field, value)
            user.save(update_fields=list(updates))
