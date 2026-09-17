import pytest
from decimal import Decimal

from django.contrib.gis.geos import Point, Polygon

from apps.geo.models import Station
from apps.ops.models import RelocationPlan, RelocationTask


@pytest.fixture
def plan(django_user):
    return RelocationPlan.objects.create(
        created_by=django_user,
        total_driver_km=Decimal("200.00"),
        algorith_used="Min-Cost Flow",
    )


@pytest.fixture
def second_station(city):
    lon, lat, d = 69.30, 41.32, 0.05
    geofence = Polygon(
        (
            (lon - d, lat - d), (lon + d, lat - d),
            (lon + d, lat + d), (lon - d, lat + d),
            (lon - d, lat - d),
        ),
        srid=4326,
    )
    return Station.objects.create(
        city=city,
        name="South Hub",
        location=Point(lon, lat, srid=4326),
        capacity=10,
        geofence=geofence,
        target_count=7,
    )


@pytest.mark.django_db
class TestRelocationTask:

    def test_creates_task(self, plan, car, station, second_station, django_user):
        task = RelocationTask.objects.create(
            plan=plan,
            car=car,
            source_station=station,
            destination_station=second_station,
            distance_km=Decimal("15.50"),
            status="PENDING",
            assigned_to=django_user,
        )
        assert task.pk is not None

    def test_car_fk_points_to_car_model(self, plan, car, station, second_station, django_user):
        task = RelocationTask.objects.create(
            plan=plan,
            car=car,
            source_station=station,
            destination_station=second_station,
            distance_km=Decimal("10.00"),
            status="PENDING",
            assigned_to=django_user,
        )
        task.refresh_from_db()
        assert task.car_id == car.pk

    def test_completed_at_auto_populated(self, plan, car, station, second_station, django_user):
        task = RelocationTask.objects.create(
            plan=plan,
            car=car,
            source_station=station,
            destination_station=second_station,
            distance_km=Decimal("8.00"),
            status="DONE",
            assigned_to=django_user,
        )
        assert task.completed_at is not None

    def test_cascade_delete_with_plan(self, plan, car, station, second_station, django_user):
        RelocationTask.objects.create(
            plan=plan,
            car=car,
            source_station=station,
            destination_station=second_station,
            distance_km=Decimal("5.00"),
            status="PENDING",
            assigned_to=django_user,
        )
        plan_pk = plan.pk
        plan.delete()
        assert RelocationTask.objects.filter(plan_id=plan_pk).count() == 0

    def test_reverse_relation_from_car(self, plan, car, station, second_station, django_user):
        RelocationTask.objects.create(
            plan=plan,
            car=car,
            source_station=station,
            destination_station=second_station,
            distance_km=Decimal("12.00"),
            status="PENDING",
            assigned_to=django_user,
        )
        assert car.relocation_tasks.count() == 1
