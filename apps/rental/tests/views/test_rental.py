import pytest
from decimal import Decimal

from rest_framework.test import APIClient

from apps.rental.enums import RentalStatus
from apps.rental.models import Rental


LIST_URL = "/api/rentals/"


def detail_url(rental_id):
    return f"/api/rentals/{rental_id}/"


def finish_url(rental_id):
    return f"/api/rentals/{rental_id}/finish/"


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user):
    api_client.force_authenticate(user=django_user)
    return api_client


def _dropoff_inside(station):
    centroid = station.geofence.centroid
    return centroid.y, centroid.x  # lat, lon


# ── list ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestListRentalsView:

    def test_returns_200_with_list(self, auth_client, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        response = auth_client.get(LIST_URL)
        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert len(response.data) == 1

    def test_response_contains_expected_fields(self, auth_client, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"), end_odometer=Decimal("10000.00"),
        )
        response = auth_client.get(LIST_URL)
        item = response.data[0]
        for field in ("id", "booking", "status", "start_odometer", "end_odometer",
                      "started_at", "ended_at", "final_price", "extra_km_charged"):
            assert field in item

    def test_filter_by_booking_id(self, auth_client, confirmed_booking,
                                   customer, car, station, pricing_rule):
        from datetime import timedelta
        from django.utils import timezone
        from psycopg2.extras import DateTimeTZRange
        from apps.booking.enums import BookingStatus
        from apps.booking.models import Booking
        now = timezone.now().replace(second=0, microsecond=0)
        other_period = DateTimeTZRange(now + timedelta(days=1), now + timedelta(days=2))
        other = Booking.objects.create(
            customer=customer, car=car, pickup_station=station,
            dropoff_station=station, pricing_rule=pricing_rule,
            period=other_period, status=BookingStatus.CONFIRMED,
            total_price=Decimal("600000.00"),
        )
        Rental.objects.create(booking=confirmed_booking, start_odometer=Decimal("0"), end_odometer=Decimal("0"))
        Rental.objects.create(booking=other, start_odometer=Decimal("0"), end_odometer=Decimal("0"))

        response = auth_client.get(LIST_URL, {"booking_id": confirmed_booking.id})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["booking"] == confirmed_booking.id

    def test_filter_by_status(self, auth_client, confirmed_booking):
        Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
            status=RentalStatus.ACTIVE,
        )
        Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
            status=RentalStatus.COMPLETED,
        )
        response = auth_client.get(LIST_URL, {"status": "active"})
        assert response.status_code == 200
        assert all(r["status"] == "active" for r in response.data)

    def test_returns_401_without_authentication(self, api_client):
        response = api_client.get(LIST_URL)
        assert response.status_code == 401

    def test_empty_list_when_no_rentals(self, auth_client):
        response = auth_client.get(LIST_URL)
        assert response.status_code == 200
        assert response.data == []


# ── create (start) ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreateRentalView:

    def test_returns_201_on_success(self, auth_client, confirmed_booking):
        payload = {"booking_id": confirmed_booking.id, "start_odometer": "10000.00"}
        response = auth_client.post(LIST_URL, payload)
        assert response.status_code == 201

    def test_response_has_active_status(self, auth_client, confirmed_booking):
        payload = {"booking_id": confirmed_booking.id, "start_odometer": "10000.00"}
        response = auth_client.post(LIST_URL, payload)
        assert response.data["status"] == RentalStatus.ACTIVE

    def test_response_has_correct_booking_id(self, auth_client, confirmed_booking):
        payload = {"booking_id": confirmed_booking.id, "start_odometer": "10000.00"}
        response = auth_client.post(LIST_URL, payload)
        assert response.data["booking"] == confirmed_booking.id

    def test_rental_saved_to_db(self, auth_client, confirmed_booking):
        payload = {"booking_id": confirmed_booking.id, "start_odometer": "10000.00"}
        auth_client.post(LIST_URL, payload)
        assert Rental.objects.filter(booking=confirmed_booking).exists()

    def test_returns_400_when_booking_id_missing(self, auth_client):
        response = auth_client.post(LIST_URL, {"start_odometer": "10000.00"})
        assert response.status_code == 400

    def test_returns_400_when_start_odometer_missing(self, auth_client, confirmed_booking):
        response = auth_client.post(LIST_URL, {"booking_id": confirmed_booking.id})
        assert response.status_code == 400

    def test_returns_404_for_nonexistent_booking(self, auth_client):
        response = auth_client.post(LIST_URL, {"booking_id": 99999, "start_odometer": "0.00"})
        assert response.status_code == 404

    def test_returns_409_when_booking_not_confirmed(self, auth_client, confirmed_booking):
        from apps.booking.enums import BookingStatus
        confirmed_booking.status = BookingStatus.PENDING
        confirmed_booking.save(update_fields=["status"])
        payload = {"booking_id": confirmed_booking.id, "start_odometer": "10000.00"}
        response = auth_client.post(LIST_URL, payload)
        assert response.status_code == 409

    def test_returns_401_without_authentication(self, api_client, confirmed_booking):
        payload = {"booking_id": confirmed_booking.id, "start_odometer": "10000.00"}
        response = api_client.post(LIST_URL, payload)
        assert response.status_code == 401


# ── retrieve ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRetrieveRentalView:

    def test_returns_200_with_correct_id(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"), end_odometer=Decimal("10000.00"),
        )
        response = auth_client.get(detail_url(rental.id))
        assert response.status_code == 200
        assert response.data["id"] == rental.id

    def test_response_shape(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"), end_odometer=Decimal("10000.00"),
        )
        response = auth_client.get(detail_url(rental.id))
        for field in ("id", "booking", "status", "start_odometer", "end_odometer",
                      "started_at", "ended_at", "final_price", "extra_km_charged"):
            assert field in response.data

    def test_returns_404_for_nonexistent_id(self, auth_client):
        response = auth_client.get(detail_url(99999))
        assert response.status_code == 404

    def test_returns_401_without_authentication(self, api_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        response = api_client.get(detail_url(rental.id))
        assert response.status_code == 401


# ── update (PUT) ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUpdateRentalView:

    def test_put_returns_200(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"), end_odometer=Decimal("10000.00"),
        )
        payload = {"end_odometer": "10500.00", "status": "completed"}
        response = auth_client.put(detail_url(rental.id), payload)
        assert response.status_code == 200

    def test_put_persists_changes(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"), end_odometer=Decimal("10000.00"),
        )
        auth_client.put(detail_url(rental.id), {"end_odometer": "10300.00"})
        rental.refresh_from_db()
        assert rental.end_odometer == Decimal("10300.00")

    def test_patch_returns_200(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        response = auth_client.patch(detail_url(rental.id), {"status": "completed"})
        assert response.status_code == 200

    def test_patch_updates_only_sent_field(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("10000.00"), end_odometer=Decimal("10000.00"),
            status=RentalStatus.ACTIVE,
        )
        auth_client.patch(detail_url(rental.id), {"end_odometer": "10200.00"})
        rental.refresh_from_db()
        assert rental.end_odometer == Decimal("10200.00")
        assert rental.start_odometer == Decimal("10000.00")
        assert rental.status == RentalStatus.ACTIVE

    def test_patch_returns_400_for_invalid_status(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        response = auth_client.patch(detail_url(rental.id), {"status": "nonexistent"})
        assert response.status_code == 400

    def test_put_returns_404_for_nonexistent_id(self, auth_client):
        response = auth_client.put(detail_url(99999), {"end_odometer": "100.00"})
        assert response.status_code == 404

    def test_patch_returns_404_for_nonexistent_id(self, auth_client):
        response = auth_client.patch(detail_url(99999), {"status": "completed"})
        assert response.status_code == 404


# ── destroy ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDestroyRentalView:

    def test_returns_204_on_success(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        response = auth_client.delete(detail_url(rental.id))
        assert response.status_code == 204

    def test_rental_removed_from_db(self, auth_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        auth_client.delete(detail_url(rental.id))
        assert not Rental.objects.filter(pk=rental.pk).exists()

    def test_returns_404_for_nonexistent_id(self, auth_client):
        response = auth_client.delete(detail_url(99999))
        assert response.status_code == 404

    def test_returns_401_without_authentication(self, api_client, confirmed_booking):
        rental = Rental.objects.create(
            booking=confirmed_booking,
            start_odometer=Decimal("0"), end_odometer=Decimal("0"),
        )
        response = api_client.delete(detail_url(rental.id))
        assert response.status_code == 401


# ── finish ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFinishRentalView:

    def _finish_payload(self, station, end_odometer="10200.00"):
        lat, lon = _dropoff_inside(station)
        return {
            "end_odometer": end_odometer,
            "dropoff_lat": lat,
            "dropoff_lon": lon,
        }

    def test_returns_200_on_success(self, auth_client, active_rental, station):
        response = auth_client.post(finish_url(active_rental.id), self._finish_payload(station))
        assert response.status_code == 200

    def test_response_status_is_completed(self, auth_client, active_rental, station):
        response = auth_client.post(finish_url(active_rental.id), self._finish_payload(station))
        assert response.data["status"] == RentalStatus.COMPLETED

    def test_response_has_final_price(self, auth_client, active_rental, station):
        response = auth_client.post(finish_url(active_rental.id), self._finish_payload(station))
        assert response.data["final_price"] is not None

    def test_response_status_is_disputed_when_damage_included(self, auth_client, active_rental, station):
        lat, lon = _dropoff_inside(station)
        payload = {
            "end_odometer": "10100.00",
            "dropoff_lat": lat,
            "dropoff_lon": lon,
            "damages": [{
                "damage_type": "SCRATCH",
                "severity": "MINOR",
                "location": "front_bumper",
                "description": "Small scratch",
                "estimated_cost": "50000.00",
            }],
        }
        response = auth_client.post(finish_url(active_rental.id), payload, format="json")
        assert response.status_code == 200
        assert response.data["status"] == RentalStatus.DISPUTED

    def test_returns_422_for_dropoff_outside_geofence(self, auth_client, active_rental):
        payload = {"end_odometer": "10100.00", "dropoff_lat": 0.0, "dropoff_lon": 0.0}
        response = auth_client.post(finish_url(active_rental.id), payload)
        assert response.status_code == 422

    def test_returns_400_when_end_odometer_missing(self, auth_client, active_rental, station):
        lat, lon = _dropoff_inside(station)
        response = auth_client.post(finish_url(active_rental.id), {"dropoff_lat": lat, "dropoff_lon": lon})
        assert response.status_code == 400

    def test_returns_400_when_dropoff_coords_missing(self, auth_client, active_rental):
        response = auth_client.post(finish_url(active_rental.id), {"end_odometer": "10100.00"})
        assert response.status_code == 400

    def test_returns_404_for_nonexistent_rental(self, auth_client, station):
        response = auth_client.post(finish_url(99999), self._finish_payload(station))
        assert response.status_code == 404

    def test_returns_409_when_rental_already_completed(self, auth_client, active_rental, station):
        active_rental.status = RentalStatus.COMPLETED
        active_rental.save(update_fields=["status"])
        response = auth_client.post(finish_url(active_rental.id), self._finish_payload(station))
        assert response.status_code == 409

    def test_returns_401_without_authentication(self, api_client, active_rental, station):
        response = api_client.post(finish_url(active_rental.id), self._finish_payload(station))
        assert response.status_code == 401
