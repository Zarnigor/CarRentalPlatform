import pytest
from datetime import timedelta
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.booking.enums import BookingStatus, RentalStatus
from apps.booking.exceptions import (
    BookingNotFoundError,
    RentalInvalidStateError,
    RentalNotFoundError,
    InvalidDropoffLocationError,
)
from apps.booking.models import Rental
from apps.booking.services.rental import RentalService
from apps.fleet.enums import CarStatus


@pytest.mark.django_db
class TestStartRental:

    def test_creates_rental_for_confirmed_booking(self, confirmed_booking):
        service = RentalService()
        rental = service.start_rental(
            booking_id=confirmed_booking.id,
            start_odometer=Decimal("10000.00"),
        )

        assert rental.id is not None
        assert rental.status == RentalStatus.ACTIVE
        assert rental.booking_id == confirmed_booking.id

    def test_sets_car_to_in_use(self, confirmed_booking):
        service = RentalService()
        service.start_rental(
            booking_id=confirmed_booking.id,
            start_odometer=Decimal("10000.00"),
        )

        confirmed_booking.car.refresh_from_db()
        assert confirmed_booking.car.status == CarStatus.IN_USE

    def test_raises_for_nonexistent_booking(self):
        service = RentalService()
        with pytest.raises(BookingNotFoundError):
            service.start_rental(booking_id=99999, start_odometer=Decimal("0.00"))

    def test_raises_when_booking_not_confirmed(self, confirmed_booking):
        confirmed_booking.status = BookingStatus.PENDING
        confirmed_booking.save(update_fields=["status"])

        service = RentalService()
        with pytest.raises(RentalInvalidStateError):
            service.start_rental(
                booking_id=confirmed_booking.id,
                start_odometer=Decimal("10000.00"),
            )


@pytest.mark.django_db
class TestFinishRental:

    @pytest.fixture
    def active_rental(self, confirmed_booking) -> Rental:
        from apps.booking.enums import PaymentKind, PaymentStatus
        from apps.booking.models import Payment
        from apps.fleet.enums import CarStatus

        confirmed_booking.car.status = CarStatus.IN_USE
        confirmed_booking.car.save(update_fields=["status"])
        Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=confirmed_booking.total_price,
            status=PaymentStatus.PROCESSING,
        )
        return Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"),
            end_odometer=Decimal("10000.00"),
            status=RentalStatus.ACTIVE,
            started_at=timezone.now() - timedelta(hours=2),
        )

    def _dropoff_inside(self, station) -> tuple[float, float]:
        """Return a point guaranteed to be inside the station geofence."""
        centroid = station.geofence.centroid
        return centroid.y, centroid.x  # lat, lon

    def test_finishes_rental_successfully(self, active_rental, station):
        lat, lon = self._dropoff_inside(station)
        service = RentalService()
        rental = service.finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10200.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )

        assert rental.status == RentalStatus.COMPLETED
        assert rental.end_odometer == Decimal("10200.00")

    def test_sets_car_back_to_available(self, active_rental, station):
        lat, lon = self._dropoff_inside(station)
        service = RentalService()
        service.finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10050.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
        )

        active_rental.booking.car.refresh_from_db()
        assert active_rental.booking.car.status == CarStatus.AVAILABLE

    def test_marks_disputed_when_damage_reported(self, active_rental, station):
        lat, lon = self._dropoff_inside(station)
        service = RentalService()
        rental = service.finish_rental(
            rental_id=active_rental.id,
            end_odometer=Decimal("10100.00"),
            dropoff_lat=lat,
            dropoff_lon=lon,
            damages=[{
                "damage_type": "SCRATCH",
                "severity": "MINOR",
                "location": "front_bumper",
                "description": "Small scratch",
                "estimated_cost": Decimal("50000.00"),
            }],
        )

        assert rental.status == RentalStatus.DISPUTED

    def test_raises_for_nonexistent_rental(self, station):
        lat, lon = self._dropoff_inside(station)
        service = RentalService()
        with pytest.raises(RentalNotFoundError):
            service.finish_rental(
                rental_id=99999,
                end_odometer=Decimal("10100.00"),
                dropoff_lat=lat,
                dropoff_lon=lon,
            )

    def test_raises_when_rental_already_completed(self, active_rental, station):
        active_rental.status = RentalStatus.COMPLETED
        active_rental.save(update_fields=["status"])

        lat, lon = self._dropoff_inside(station)
        service = RentalService()
        with pytest.raises(RentalInvalidStateError):
            service.finish_rental(
                rental_id=active_rental.id,
                end_odometer=Decimal("10100.00"),
                dropoff_lat=lat,
                dropoff_lon=lon,
            )

    def test_raises_for_dropoff_outside_geofence(self, active_rental):
        service = RentalService()
        # Far-away point guaranteed to be outside the small station geofence.
        with pytest.raises(InvalidDropoffLocationError):
            service.finish_rental(
                rental_id=active_rental.id,
                end_odometer=Decimal("10100.00"),
                dropoff_lat=0.0,
                dropoff_lon=0.0,
            )
