import pytest
from datetime import date

from apps.accounts.enums import CustomerTier
from apps.accounts.models import CustomUser, Customer


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(username="driver1", password="pw")


@pytest.mark.django_db
class TestCustomer:

    def test_creates_customer_with_required_fields(self, user):
        customer = Customer.objects.create(
            user=user,
            license_no="DL99887",
            license_verified_at=date(2023, 6, 1),
        )
        assert customer.pk is not None

    def test_risk_score_defaults_to_zero(self, user):
        customer = Customer.objects.create(
            user=user,
            license_no="DL00001",
            license_verified_at=date(2023, 1, 1),
        )
        assert customer.risk_score == 0.0

    def test_tier_defaults_to_standard(self, user):
        customer = Customer.objects.create(
            user=user,
            license_no="DL00002",
            license_verified_at=date(2023, 1, 1),
        )
        assert customer.tier == CustomerTier.STANDARD

    def test_all_tiers_are_valid(self):
        for i, tier in enumerate(CustomerTier.values):
            u = CustomUser.objects.create_user(username=f"tier_user_{i}", password="pw")
            c = Customer.objects.create(
                user=u,
                license_no=f"DL{i:05d}",
                license_verified_at=date(2023, 1, 1),
                tier=tier,
            )
            assert c.tier == tier

    def test_cascade_delete_with_user(self, user):
        Customer.objects.create(
            user=user,
            license_no="DL77777",
            license_verified_at=date(2023, 1, 1),
        )
        user.delete()
        assert Customer.objects.filter(license_no="DL77777").count() == 0

    def test_license_no_max_length(self):
        field = Customer._meta.get_field("license_no")
        assert field.max_length == 20
