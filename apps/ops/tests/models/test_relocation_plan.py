import pytest
from decimal import Decimal

from apps.ops.models import RelocationPlan


@pytest.mark.django_db
class TestRelocationPlan:

    def test_creates_plan(self, django_user):
        plan = RelocationPlan.objects.create(
            created_by=django_user,
            total_driver_km=Decimal("120.50"),
            algorith_used="Hungarian",
        )
        assert plan.pk is not None

    def test_created_at_auto_populated(self, django_user):
        plan = RelocationPlan.objects.create(
            created_by=django_user,
            total_driver_km=Decimal("50.00"),
            algorith_used="Greedy",
        )
        assert plan.created_at is not None

    def test_algorith_used_max_length(self):
        field = RelocationPlan._meta.get_field("algorith_used")
        assert field.max_length == 200

    def test_cascade_delete_with_user(self, django_user):
        RelocationPlan.objects.create(
            created_by=django_user,
            total_driver_km=Decimal("10.00"),
            algorith_used="Greedy",
        )
        django_user.delete()
        assert RelocationPlan.objects.count() == 0
