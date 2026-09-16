# tests/services/test_booking_service.py

import pytest
import uuid
from datetime import timedelta
from psycopg2.extras import DateTimeTZRange

from apps.booking.services import BookingService
from apps.booking.enums import BookingStatus
from apps.booking.exceptions import CarNotAvailableForPeriodError


@pytest.mark.django_db
class TestCreateBooking:

    def test_creates_booking_successfully(self, customer, car, station, booking_period):
        service = BookingService()

        booking = service.create_booking(
            customer=customer,
            car_id=car.id,
            pickup_station_id=station.id,
            dropoff_station_id=station.id,
            period=booking_period,
            total_price=100000,
            idempotency_key=uuid.uuid4(),
        )

        assert booking.id is not None
        assert booking.status == BookingStatus.PENDING
        assert booking.car_id == car.id

    def test_returns_same_booking_for_same_idempotency_key(self, customer, car, station, booking_period):
        service = BookingService()
        key = uuid.uuid4()

        booking1 = service.create_booking(
            customer=customer, car_id=car.id,
            pickup_station_id=station.id, dropoff_station_id=station.id,
            period=booking_period, total_price=100000, idempotency_key=key,
        )

        booking2 = service.create_booking(
            customer=customer, car_id=car.id,
            pickup_station_id=station.id, dropoff_station_id=station.id,
            period=booking_period, total_price=100000, idempotency_key=key,
        )

        assert booking1.id == booking2.id  # ikkinchi chaqiruv YANGI booking yaratmadi

    def test_raises_when_car_already_booked_for_overlapping_period(
        self, customer, car, station, booking_period
    ):
        service = BookingService()

        # birinchi booking — muvaffaqiyatli
        service.create_booking(
            customer=customer, car_id=car.id,
            pickup_station_id=station.id, dropoff_station_id=station.id,
            period=booking_period, total_price=100000, idempotency_key=uuid.uuid4(),
        )

        # ikkinchi booking — kesishuvchi vaqt, xato kutilmoqda
        overlapping_period = DateTimeTZRange(
            booking_period.lower + timedelta(hours=1),
            booking_period.upper + timedelta(hours=1),
        )

        with pytest.raises(CarNotAvailableForPeriodError):
            service.create_booking(
                customer=customer, car_id=car.id,
                pickup_station_id=station.id, dropoff_station_id=station.id,
                period=overlapping_period, total_price=100000, idempotency_key=uuid.uuid4(),
            )

    def test_allows_non_overlapping_period_for_same_car(
        self, customer, car, station, booking_period
    ):
        service = BookingService()

        service.create_booking(
            customer=customer, car_id=car.id,
            pickup_station_id=station.id, dropoff_station_id=station.id,
            period=booking_period, total_price=100000, idempotency_key=uuid.uuid4(),
        )

        # kesishmaydigan vaqt — muammosiz o'tishi kerak
        non_overlapping_period = DateTimeTZRange(
            booking_period.upper + timedelta(hours=1),
            booking_period.upper + timedelta(hours=5),
        )

        booking2 = service.create_booking(
            customer=customer, car_id=car.id,
            pickup_station_id=station.id, dropoff_station_id=station.id,
            period=non_overlapping_period, total_price=100000, idempotency_key=uuid.uuid4(),
        )

        assert booking2.id is not None