import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from django.core.management import BaseCommand
from django.utils import timezone
from faker import Faker
from faker_vehicle import VehicleProvider
from psycopg2.extras import DateTimeTZRange

from apps.accounts.enums import CustomerTier
from apps.accounts.models import CustomUser, Customer
from apps.booking.enums import BookingStatus, PaymentStatus, PaymentKind
from apps.booking.models.booking import Booking
from apps.booking.models.payment import Payment
from apps.fleet.enums import TransmissionType, FuelType, CarStatus
from apps.fleet.models import CarModel, Car
from apps.geo.models import City, Station
from apps.ops.enums import PricingScope, PricingRuleType
from apps.ops.models.pricing_rule import PricingRule
from apps.ops.models.relocation_plan import RelocationPlan
from apps.ops.models.relocation_task import RelocationTask

BATCH = 10_000


class Command(BaseCommand):
    help = "Seed the database with large volumes of fake data for load testing"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=1_000_000)
        parser.add_argument("--clear", action="store_true", help="Delete existing data before seeding")

    def handle(self, *args, **options):
        fake = Faker()
        fake.add_provider(VehicleProvider)
        count = options["count"]

        if options["clear"]:
            self._clear()

        self._seed_cities(fake)
        self._seed_stations(fake)
        self._seed_users_and_customers(fake, count)
        self._seed_car_models(fake, count)
        self._seed_cars(fake, count)
        self._seed_pricing_rules(fake, count)
        self._seed_bookings(fake, count)
        self._seed_payments(fake, count)
        self._seed_relocation_plans(fake, count)
        self._seed_relocation_tasks(fake, count)

        self.stdout.write(self.style.SUCCESS("=== Seeding complete ==="))

    # ─── helpers ───────────────────────────────────────────────────────────────

    def _bulk(self, model, objs, label, ignore_conflicts=True):
        total = 0
        buf = []
        for obj in objs:
            buf.append(obj)
            if len(buf) >= BATCH:
                model.objects.bulk_create(buf, ignore_conflicts=ignore_conflicts)
                total += len(buf)
                buf = []
                self.stdout.write(f"  {label}: {total:,}", ending="\r")
                self.stdout.flush()
        if buf:
            model.objects.bulk_create(buf, ignore_conflicts=ignore_conflicts)
            total += len(buf)
        self.stdout.write(self.style.SUCCESS(f"  {label}: {total:,} rows inserted"))
        return total

    @staticmethod
    def _box(lon, lat, delta=0.01):
        coords = (
            (lon - delta, lat - delta),
            (lon + delta, lat - delta),
            (lon + delta, lat + delta),
            (lon - delta, lat + delta),
            (lon - delta, lat - delta),
        )
        return Polygon(coords, srid=4326)

    # ─── clear ─────────────────────────────────────────────────────────────────

    def _clear(self):
        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        for model in (
            RelocationTask, RelocationPlan,
            Payment, Booking,
            PricingRule, Car, CarModel,
            Customer, CustomUser,
            Station, City,
        ):
            count, _ = model.objects.all().delete()
            self.stdout.write(f"  {model.__name__}: {count:,} deleted")
        self.stdout.write(self.style.WARNING("Done clearing."))

    # ─── geo ───────────────────────────────────────────────────────────────────

    def _seed_cities(self, fake):
        self.stdout.write("Seeding cities...")

        def gen():
            for _ in range(50):
                lon = float(fake.longitude())
                lat = float(fake.latitude())
                yield City(
                    name=fake.city()[:30],
                    timezone=fake.timezone(),
                    boundary=MultiPolygon(self._box(lon, lat, delta=0.5), srid=4326),
                )

        self._bulk(City, gen(), "City")

    def _seed_stations(self, fake):
        self.stdout.write("Seeding stations...")
        city_ids = list(City.objects.values_list("id", flat=True))

        def gen():
            for city_id in city_ids:
                for _ in range(20):
                    lon = float(fake.longitude())
                    lat = float(fake.latitude())
                    yield Station(
                        city_id=city_id,
                        name=fake.street_name()[:30],
                        location=Point(lon, lat, srid=4326),
                        capacity=random.randint(5, 50),
                        geofence=self._box(lon, lat, delta=0.005),
                        target_count=random.randint(3, 30),
                    )

        self._bulk(Station, gen(), "Station")

    # ─── accounts ──────────────────────────────────────────────────────────────

    def _seed_users_and_customers(self, fake, count):
        self.stdout.write(f"Seeding {count:,} users...")
        prefix = uuid.uuid4().hex[:8]
        tiers = [c[0] for c in CustomerTier.choices]

        def gen_users():
            for i in range(count):
                yield CustomUser(
                    username=f"{prefix}_{i}",
                    email=f"{prefix}_{i}@seed.test",
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    is_active=True,
                )

        self._bulk(CustomUser, gen_users(), "CustomUser", ignore_conflicts=True)

        self.stdout.write(f"Seeding {count:,} customers...")
        user_ids = list(
            CustomUser.objects.filter(username__startswith=prefix)
            .values_list("id", flat=True)
        )

        def gen_customers():
            for uid in user_ids:
                yield Customer(
                    user_id=uid,
                    passport_code=fake.bothify(text="??#######"),
                    license_no=fake.bothify(text="??####??"),
                    license_verified_at=fake.date_this_decade(),
                    risk_score=round(random.uniform(0, 1), 4),
                    tier=random.choice(tiers),
                )

        self._bulk(Customer, gen_customers(), "Customer", ignore_conflicts=True)

    # ─── fleet ─────────────────────────────────────────────────────────────────

    def _seed_car_models(self, fake, count):
        self.stdout.write(f"Seeding {count:,} car models...")
        transmissions = [c[0] for c in TransmissionType.choices]
        fuels = [c[0] for c in FuelType.choices]

        def gen():
            for _ in range(count):
                veh = fake.vehicle_object()
                yield CarModel(
                    brand=veh["Make"][:200],
                    model=veh["Model"][:200],
                    seats=random.randint(2, 8),
                    transmission=random.choice(transmissions),
                    fuel_type=random.choice(fuels),
                    daily_base_price=Decimal(str(round(random.uniform(20, 500), 2))),
                )

        self._bulk(CarModel, gen(), "CarModel")

    def _seed_cars(self, fake, count):
        self.stdout.write(f"Seeding {count:,} cars...")
        car_model_ids = list(CarModel.objects.values_list("id", flat=True))
        station_ids = list(Station.objects.values_list("id", flat=True))
        statuses = [c[0] for c in CarStatus.choices]
        prefix = uuid.uuid4().hex[:6].upper()

        def gen():
            for i in range(count):
                lon = float(fake.longitude())
                lat = float(fake.latitude())
                yield Car(
                    carModel_id=random.choice(car_model_ids),
                    plate=f"{prefix}{i:07d}",
                    station_id=random.choice(station_ids),
                    status=random.choice(statuses),
                    current_location=Point(lon, lat, srid=4326),
                    odometer_km=random.randint(0, 300_000),
                    fuel_level=random.randint(0, 100),
                    year=random.randint(2000, 2024),
                )

        self._bulk(Car, gen(), "Car", ignore_conflicts=True)

    # ─── ops ───────────────────────────────────────────────────────────────────

    def _seed_pricing_rules(self, fake, count):
        self.stdout.write(f"Seeding {count:,} pricing rules...")
        scopes = [c[0] for c in PricingScope.choices]
        rule_types = [c[0] for c in PricingRuleType.choices]
        now = timezone.now()

        def gen():
            for _ in range(count):
                start = now - timedelta(days=random.randint(0, 365))
                end = start + timedelta(days=random.randint(30, 730))
                yield PricingRule(
                    name=fake.bs()[:255],
                    scope=random.choice(scopes),
                    rule_type=random.choice(rule_types),
                    priority=random.randint(0, 100),
                    valid_period=DateTimeTZRange(start, end),
                    multiplier=Decimal(str(round(random.uniform(0.5, 3.0), 2))),
                    flat_fee=Decimal(str(round(random.uniform(0, 100), 2))),
                    is_active=random.choice([True, False]),
                    price_per_day=Decimal(str(round(random.uniform(10, 500), 2))),
                    free_km_per_day=random.randint(0, 300),
                    price_per_extra_km=Decimal(str(round(random.uniform(0.1, 5.0), 2))),
                )

        self._bulk(PricingRule, gen(), "PricingRule")

    # ─── booking ───────────────────────────────────────────────────────────────

    def _seed_bookings(self, fake, count):
        self.stdout.write(f"Seeding {count:,} bookings...")
        customer_ids = list(Customer.objects.values_list("id", flat=True))
        car_ids = list(Car.objects.values_list("id", flat=True))
        station_ids = list(Station.objects.values_list("id", flat=True))
        pricing_rule_ids = list(PricingRule.objects.values_list("id", flat=True))
        # Only terminal statuses — avoids the car+period exclusion constraint
        safe_statuses = [
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED,
            BookingStatus.EXPIRED,
            BookingStatus.PAYMENT_FAILED,
        ]
        now = timezone.now()

        def gen():
            for _ in range(count):
                start = now - timedelta(days=random.randint(1, 730))
                end = start + timedelta(hours=random.randint(1, 720))
                yield Booking(
                    customer_id=random.choice(customer_ids),
                    car_id=random.choice(car_ids),
                    pickup_station_id=random.choice(station_ids),
                    dropoff_station_id=random.choice(station_ids),
                    pricing_rule_id=random.choice(pricing_rule_ids) if random.random() > 0.2 else None,
                    period=DateTimeTZRange(start, end),
                    status=random.choice(safe_statuses),
                    total_price=Decimal(str(round(random.uniform(20, 2000), 2))),
                )

        self._bulk(Booking, gen(), "Booking", ignore_conflicts=True)

    def _seed_payments(self, fake, count):
        self.stdout.write(f"Seeding {count:,} payments...")
        booking_ids = list(Booking.objects.values_list("id", flat=True))
        statuses = [c[0] for c in PaymentStatus.choices]
        kinds = [c[0] for c in PaymentKind.choices]

        def gen():
            for _ in range(count):
                yield Payment(
                    booking_id=random.choice(booking_ids),
                    kind=random.choice(kinds),
                    amount=Decimal(str(round(random.uniform(10, 2000), 2))),
                    status=random.choice(statuses),
                )

        self._bulk(Payment, gen(), "Payment")

    # ─── relocation ────────────────────────────────────────────────────────────

    def _seed_relocation_plans(self, fake, count):
        self.stdout.write(f"Seeding {count:,} relocation plans...")
        user_ids = list(CustomUser.objects.values_list("id", flat=True))
        algos = ["nearest_neighbor", "genetic", "simulated_annealing", "greedy", "dijkstra"]

        def gen():
            for _ in range(count):
                yield RelocationPlan(
                    created_by_id=random.choice(user_ids),
                    total_driver_km=Decimal(str(round(random.uniform(10, 10_000), 2))),
                    algorith_used=random.choice(algos),
                )

        self._bulk(RelocationPlan, gen(), "RelocationPlan")

    def _seed_relocation_tasks(self, fake, count):
        self.stdout.write(f"Seeding {count:,} relocation tasks...")
        plan_ids = list(RelocationPlan.objects.values_list("id", flat=True))
        car_ids = list(Car.objects.values_list("id", flat=True))
        station_ids = list(Station.objects.values_list("id", flat=True))
        user_ids = list(CustomUser.objects.values_list("id", flat=True))
        task_statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"]

        def gen():
            for _ in range(count):
                yield RelocationTask(
                    plan_id=random.choice(plan_ids),
                    car_id=random.choice(car_ids),
                    source_station_id=random.choice(station_ids),
                    destination_station_id=random.choice(station_ids),
                    distance_km=Decimal(str(round(random.uniform(1, 500), 2))),
                    status=random.choice(task_statuses),
                    assigned_to_id=random.choice(user_ids),
                )

        self._bulk(RelocationTask, gen(), "RelocationTask")
