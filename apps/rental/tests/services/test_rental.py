import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.booking.enums import BookingStatus
from apps.booking.exceptions import BookingNotFoundError
from apps.damage.models import Damage
from apps.fleet.enums import CarStatus
from apps.rental.enums import RentalStatus
from apps.rental.exceptions import (
    InvalidDropoffLocationError,
    RentalInvalidStateError,
    RentalNotFoundError,
)
from apps.rental.models import Rental
from apps.rental.services import RentalService


# ── helpers ───────────────────────────────────────────────────────────────────

def _dropoff_inside(station):
    centroid = station.geofence.centroid
    return centroid.y, centroid.x  # lat, lon


_DAMAGE = {
    "damage_type": "SCRATCH",
    "severity": "MINOR",
    "location": "front_bumper",
    "description": "Small scratch",
    "estimated_cost": Decimal("50000.00"),
}


# ── list ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestListRentals:

    def test_returns_all_rentals(self, confirmed_booking):
        Rental.objects.create(booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"))
        Rental.objects.create(booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"))
        qs = RentalService().list_rentals()
        assert qs.count() == 2

    def test_filter_by_booking_id(self, confirmed_booking, customer, car, station, pricing_rule):
        from datetime import timedelta
        from django.utils import timezone
        from psycopg2.extras import DateTimeTZRange
        from apps.booking.models import Booking
        now = timezone.now().replace(second=0, microsecond=0)
        other_period = DateTimeTZRange(now + timedelta(days=1), now + timedelta(days=2))
        other_booking = Booking.objects.create(
            customer=customer, car=car, pickup_station=station,
            dropoff_station=station, pricing_rule=pricing_rule,
            period=other_period, status=BookingStatus.CONFIRMED,
            total_price=Decimal("600000.00"),
        )
        Rental.objects.create(booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"))
        Rental.objects.create(booking=other_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"))

        qs = RentalService().list_rentals(booking_id=confirmed_booking.id)
        assert qs.count() == 1
        assert qs.first().booking_id == confirmed_booking.id

    def test_filter_by_status(self, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"),
            status=RentalStatus.ACTIVE,
        )
        Rental.objects.create(
            booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"),
            status=RentalStatus.COMPLETED,
        )
        qs = RentalService().list_rentals(status=RentalStatus.ACTIVE)
        assert all(r.status == RentalStatus.ACTIVE for r in qs)
        assert qs.count() == 1

    def test_returns_empty_queryset_when_no_match(self, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"),
            status=RentalStatus.ACTIVE,
        )
        qs = RentalService().list_rentals(status=RentalStatus.COMPLETED)
        assert qs.count() == 0

    def test_returns_empty_queryset_with_no_rentals(self):
        qs = RentalService().list_rentals()
        assert qs.count() == 0


# ── get ───────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetRental:

    def test_returns_rental_by_id(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        result = RentalService().get_rental(rental_id=rental.id)
        assert result.id == rental.id

    def test_raises_for_nonexistent_id(self):
        with pytest.raises(RentalNotFoundError):
            RentalService().get_rental(rental_id=99999)


# ── update ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUpdateRental:

    def test_updates_single_field(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        updated = RentalService().update_rental(rental_id=rental.id, end_odometer=Decimal("500.00"))
        assert updated.end_odometer == Decimal("500.00")

    def test_persists_update_to_db(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        RentalService().update_rental(rental_id=rental.id, status=RentalStatus.COMPLETED)
        rental.refresh_from_db()
        assert rental.status == RentalStatus.COMPLETED

    def test_updates_multiple_fields_at_once(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        updated = RentalService().update_rental(
            rental_id=rental.id,
            end_odometer=Decimal("200.00"),
            final_price=Decimal("150000.00"),
            status=RentalStatus.COMPLETED,
        )
        assert updated.end_odometer == Decimal("200.00")
        assert updated.final_price == Decimal("150000.00")
        assert updated.status == RentalStatus.COMPLETED

    def test_does_not_touch_unspecified_fields(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"),
            end_odometer=Decimal("10000.00"),
            status=RentalStatus.ACTIVE,
        )
        RentalService().update_rental(rental_id=rental.id, end_odometer=Decimal("10500.00"))
        rental.refresh_from_db()
        assert rental.start_odometer == Decimal("10000.00")
        assert rental.status == RentalStatus.ACTIVE

    def test_raises_for_nonexistent_id(self):
        with pytest.raises(RentalNotFoundError):
            RentalService().update_rental(rental_id=99999, status=RentalStatus.COMPLETED)


# ── delete ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDeleteRental:

    def test_deletes_rental(self, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        RentalService().delete_rental(rental_id=rental.id)
        assert not Rental.objects.filter(pk=rental.pk).exists()

    def test_raises_for_nonexistent_id(self):
        with pytest.raises(RentalNotFoundError):
            RentalService().delete_rental(rental_id=99999)


# ── start ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStartRental:

    def test_creates_rental_for_confirmed_booking(self, confirmed_booking):
        rental = RentalService().start_rental(
            booking_id=confirmed_booking.id,
            start_odometer=Decimal("10000.00"),
        )
        assert rental.id is not None
        assert rental.status == RentalStatus.ACTIVE
        assert rental.booking_id == confirmed_booking.id

    def test_sets_started_at(self, confirmed_booking):
        before = timezone.now()
        rental = RentalService().start_rental(
            booking_id=confirmed_booking.id,
            start_odometer=Decimal("10000.00"),
        )
        assert rental.started_at >= before

    def test_end_odometer_equals_start_odometer_on_creation(self, confirmed_booking):
        rental = RentalService().start_rental(
            booking_id=confirmed_booking.id,
            start_odometer=Decimal("10000.00"),
        )
        assert rental.end_odometer == Decimal("10000.00")

    def test_sets_car_to_in_use(self, confirmed_booking):
        RentalService().start_rental(
            booking_id=confirmed_booking.id,
            start_odometer=Decimal("10000.00"),
        )
        confirmed_booking.car.refresh_from_db()
        assert confirmed_booking.car.status == CarStatus.IN_USE

    def test_raises_for_nonexistent_booking(self):
        with pytest.raises(BookingNotFoundError):
            RentalService().start_rental(booking_id=99999, start_odometer=Decimal("0.00"))

    def test_raises_when_booking_not_confirmed(self, confirmed_booking):
        confirmed_booking.status = BookingStatus.PENDING
        confirmed_booking.save(update_fields=["status"])
        with pytest.raises(RentalInvalidStateError):
            RentalService().start_rental(
                booking_id=confirmed_booking.id,
                start_odometer=Decimal("10000.00"),
            )


# ── finish ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFinishRental:

    def test_finishes_rental_successfully(self, active_rental, station):
        lat, lon = _dropoff_inside(station)
        rental = RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10200.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )
        assert rental.status == RentalStatus.COMPLETED
        assert rental.end_odometer == Decimal("10200.00")

    def test_sets_ended_at(self, active_rental, station):
        lat, lon = _dropoff_inside(station)
        before = timezone.now()
        rental = RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10200.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )
        assert rental.ended_at >= before

    def test_final_price_is_persisted(self, active_rental, station):
        lat, lon = _dropoff_inside(station)
        rental = RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10050.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )
        active_rental.refresh_from_db()
        assert active_rental.final_price is not None
        assert active_rental.final_price == rental.final_price

    def test_no_extra_km_when_within_free_limit(self, active_rental, station):
        # pricing_rule has free_km_per_day=100; odometer delta=50 → no extra
        lat, lon = _dropoff_inside(station)
        rental = RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10050.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )
        assert rental.extra_km_charged == Decimal("0")

    def test_extra_km_charged_when_over_free_limit(self, active_rental, station):
        # pricing_rule: free_km_per_day=100, price_per_extra_km=500
        # delta = 200 km, 1 day → 100 free, 100 extra → 100 × 500 = 50000
        lat, lon = _dropoff_inside(station)
        rental = RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10200.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )
        assert rental.extra_km_charged == Decimal("50000.00")

    def test_sets_car_back_to_available(self, active_rental, station):
        lat, lon = _dropoff_inside(station)
        RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10050.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )
        active_rental.booking.car.refresh_from_db()
        assert active_rental.booking.car.status == CarStatus.AVAILABLE

    def test_marks_disputed_and_car_to_maintenance_when_damage_reported(self, active_rental, station):
        lat, lon = _dropoff_inside(station)
        rental = RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10100.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
            damages=[_DAMAGE],
        )
        assert rental.status == RentalStatus.DISPUTED
        active_rental.booking.car.refresh_from_db()
        assert active_rental.booking.car.status == CarStatus.MAINTENANCE

    def test_damage_record_created_in_db(self, active_rental, station):
        lat, lon = _dropoff_inside(station)
        RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10100.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
            damages=[_DAMAGE],
        )
        assert Damage.objects.filter(rental=active_rental).count() == 1

    def test_multiple_damages_all_saved(self, active_rental, station):
        lat, lon = _dropoff_inside(station)
        RentalService().finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10100.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
            damages=[_DAMAGE, {**_DAMAGE, "location": "rear_bumper"}],
        )
        assert Damage.objects.filter(rental=active_rental).count() == 2

    def test_raises_for_nonexistent_rental(self, station):
        lat, lon = _dropoff_inside(station)
        with pytest.raises(RentalNotFoundError):
            RentalService().finish_rental(
                rental_id=99999,
                end_odometer=Decimal("10100.00"),
                dropoff_lat=lat,
                dropoff_lon=lon,
            )

    def test_raises_when_rental_not_active(self, active_rental, station):
        active_rental.status = RentalStatus.COMPLETED
        active_rental.save(update_fields=["status"])
        lat, lon = _dropoff_inside(station)
        with pytest.raises(RentalInvalidStateError):
            RentalService().finish_rental(
                rental_id=active_rental.id,
                end_odometer=Decimal("10100.00"),
                dropoff_lat=lat,
                dropoff_lon=lon,
            )

    def test_raises_for_dropoff_outside_geofence(self, active_rental):
        with pytest.raises(InvalidDropoffLocationError):
            RentalService().finish_rental(
                rental_id=active_rental.id,
                end_odometer=Decimal("10100.00"),
                dropoff_lat=0.0,
                dropoff_lon=0.0,
            )
