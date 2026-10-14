import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from apps.booking.enums import BookingStatus
from apps.booking.exceptions import BookingNotFoundError
from apps.booking.models import Booking
from apps.booking.services import BookingService


def _make_booking(customer, car, station, pricing_rule, offset_days=1):
    now = timezone.now().replace(second=0, microsecond=0)
    period = DateTimeTZRange(
        now + timedelta(days=offset_days),
        now + timedelta(days=offset_days, hours=4),
    )
    return Booking.objects.create(
        customer=customer,
        car=car,
        pickup_station=station,
        dropoff_station=station,
        pricing_rule=pricing_rule,
        period=period,
        status=BookingStatus.CONFIRMED,
        total_price=Decimal("600000.00"),
    )


@pytest.mark.django_db
class TestBookingServiceListBookings:

    def test_returns_all_bookings(self, confirmed_booking):
        qs = BookingService().list_bookings()
        assert qs.count() >= 1

    def test_filter_by_customer_id(self, confirmed_booking, customer):
        qs = BookingService().list_bookings(customer_id=customer.id)
        assert all(b.customer_id == customer.id for b in qs)
        assert qs.count() >= 1

    def test_filter_by_status(self, confirmed_booking):
        qs = BookingService().list_bookings(status=BookingStatus.CONFIRMED)
        assert all(b.status == BookingStatus.CONFIRMED for b in qs)

    def test_filter_by_car_id(self, confirmed_booking, car):
        qs = BookingService().list_bookings(car_id=car.id)
        assert all(b.car_id == car.id for b in qs)
        assert qs.count() >= 1

    def test_filter_by_status_excludes_others(self, confirmed_booking):
        confirmed_booking.status = BookingStatus.CANCELLED
        confirmed_booking.save(update_fields=["status"])
        qs = BookingService().list_bookings(status=BookingStatus.CONFIRMED)
        assert confirmed_booking not in list(qs)

    def test_combined_filters(self, confirmed_booking, customer, car):
        qs = BookingService().list_bookings(
            customer_id=customer.id,
            car_id=car.id,
            status=BookingStatus.CONFIRMED,
        )
        assert all(
            b.customer_id == customer.id and b.car_id == car.id
            for b in qs
        )

    def test_returns_empty_when_no_match(self, confirmed_booking):
        qs = BookingService().list_bookings(customer_id=99999)
        assert qs.count() == 0


@pytest.mark.django_db
class TestBookingServiceGetBooking:

    def test_returns_booking_by_id(self, confirmed_booking):
        result = BookingService().get_booking(booking_id=confirmed_booking.id)
        assert result.pk == confirmed_booking.pk

    def test_raises_for_nonexistent_id(self):
        with pytest.raises(BookingNotFoundError):
            BookingService().get_booking(booking_id=99999)

    def test_result_has_related_objects_loaded(self, confirmed_booking):
        result = BookingService().get_booking(booking_id=confirmed_booking.id)
        assert result.customer is not None
        assert result.car is not None
        assert result.pickup_station is not None
        assert result.dropoff_station is not None


@pytest.mark.django_db
class TestBookingServiceUpdateBooking:

    def test_updates_status(self, confirmed_booking):
        updated = BookingService().update_booking(
            booking_id=confirmed_booking.id,
            status=BookingStatus.CANCELLED,
        )
        assert updated.status == BookingStatus.CANCELLED

    def test_persists_update_to_db(self, confirmed_booking):
        BookingService().update_booking(
            booking_id=confirmed_booking.id,
            status=BookingStatus.ACTIVE,
        )
        confirmed_booking.refresh_from_db()
        assert confirmed_booking.status == BookingStatus.ACTIVE

    def test_updates_total_price(self, confirmed_booking):
        updated = BookingService().update_booking(
            booking_id=confirmed_booking.id,
            total_price=Decimal("999000.00"),
        )
        assert updated.total_price == Decimal("999000.00")

    def test_does_not_touch_unspecified_fields(self, confirmed_booking):
        original_price = confirmed_booking.total_price
        BookingService().update_booking(
            booking_id=confirmed_booking.id,
            status=BookingStatus.ACTIVE,
        )
        confirmed_booking.refresh_from_db()
        assert confirmed_booking.total_price == original_price

    def test_raises_for_nonexistent_booking(self):
        with pytest.raises(BookingNotFoundError):
            BookingService().update_booking(
                booking_id=99999,
                status=BookingStatus.CANCELLED,
            )


@pytest.mark.django_db
class TestBookingServiceDeleteBooking:

    def test_deletes_booking(self, confirmed_booking):
        pk = confirmed_booking.pk
        BookingService().delete_booking(booking_id=confirmed_booking.id)
        assert not Booking.objects.filter(pk=pk).exists()

    def test_raises_for_nonexistent_booking(self):
        with pytest.raises(BookingNotFoundError):
            BookingService().delete_booking(booking_id=99999)
