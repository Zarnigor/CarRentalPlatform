from decimal import Decimal
from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils import timezone
from apps.booking.enums import BookingStatus, RentalStatus
from apps.booking.exceptions import (
    RentalNotFoundError,
    RentalInvalidStateError,
    InvalidDropoffLocationError,
    DamageRecordInvalidError,
)
from apps.booking.models import Rental, Damage, Booking
from apps.booking.services.payment import PaymentService
from apps.fleet.enums import CarStatus


class RentalService:

    def start_rental(self, *, booking_id: int, start_odometer: Decimal) -> Rental:
        """
        Booking tasdiqlangan bo'lsa, Rental yaratadi va uni ACTIVE holatga o'tkazadi.
        Car statusini IN_USE ga o'zgartiradi.
        """
        with transaction.atomic():
            try:
                booking = Booking.objects.select_for_update().get(id=booking_id)
            except Booking.DoesNotExist:
                from apps.booking.exceptions import BookingNotFoundError
                raise BookingNotFoundError(booking_id=booking_id)

            if booking.status != BookingStatus.CONFIRMED:
                raise RentalInvalidStateError(
                    rental_id=None, current_status=booking.status
                )

            rental = Rental.objects.create(
                booking=booking,
                started_at=timezone.now(),
                start_odometer=start_odometer,
                end_odometer=start_odometer,
                status=RentalStatus.ACTIVE,
            )

            car = booking.car
            car.status = CarStatus.IN_USE
            car.save(update_fields=["status"])

            return rental

    def finish_rental(
        self, *,
        rental_id: int,
        end_odometer: Decimal,
        dropoff_lat: float,
        dropoff_lon: float,
        damages: list[dict] | None = None,
    ) -> Rental:
        """
        Rentalni yakunlaydi: narxni qayta hisoblaydi, geofence'ni tekshiradi,
        damage yozuvlarini saqlaydi, Car statusini yangilaydi.
        """
        damages = damages or []

        with transaction.atomic():
            try:
                rental = Rental.objects.select_for_update().get(id=rental_id)
            except Rental.DoesNotExist:
                raise RentalNotFoundError(rental_id=rental_id)

            if rental.status != RentalStatus.ACTIVE:
                raise RentalInvalidStateError(
                    rental_id=rental_id, current_status=rental.status
                )

            booking = rental.booking
            car = booking.car

            # Geofence tekshiruvi
            dropoff_point = Point(dropoff_lon, dropoff_lat, srid=4326)
            station = booking.dropoff_station

            if not station.geofence.contains(dropoff_point):
                raise InvalidDropoffLocationError(
                    rental_id=rental_id, lat=dropoff_lat, lon=dropoff_lon
                )

            # pricing
            final_price, extra_km_charged = self._calculate_final_price(
                rental=rental, end_odometer=end_odometer
            )

            rental.ended_at = timezone.now()
            rental.end_odometer = end_odometer
            rental.final_price = final_price
            rental.extra_km_charged = extra_km_charged
            rental.status = RentalStatus.COMPLETED

            # Damage
            has_damage = False
            for damage_data in damages:
                self._create_damage(rental=rental, damage_data=damage_data)
                has_damage = True

            if has_damage:
                rental.status = RentalStatus.DISPUTED

            rental.save(update_fields=[
                "ended_at", "end_odometer", "final_price",
                "extra_km_charged", "status",
            ])

            # 4. Car statusi + odometr
            car.odometer_km = int(end_odometer)
            if rental.status == RentalStatus.COMPLETED:
                car.status = CarStatus.AVAILABLE
            else:
                car.status = CarStatus.MAINTENANCE
            car.save(update_fields=["status", "odometer_km"])

            # 5. To'lov
            if rental.status == RentalStatus.COMPLETED:
                payment_service = PaymentService()
                payment_service.release_hold(booking=booking)
                payment_service.capture_final_amount(booking=booking, final_amount=rental.final_price)

            return rental

    def _calculate_final_price(self, *, rental: Rental, end_odometer: Decimal) -> tuple[Decimal, Decimal]:
        booking = rental.booking
        pricing_rule = booking.pricing_rule

        if pricing_rule is None:
            from apps.booking.exceptions import PricingRuleNotFoundError
            raise PricingRuleNotFoundError(car_model_id=booking.car.id)

        days = max(1, (timezone.now() - rental.started_at).days)
        base_price = pricing_rule.price_per_day * days

        distance_km = end_odometer - rental.start_odometer
        free_km_limit = pricing_rule.free_km_per_day * days
        extra_km = max(Decimal("0"), distance_km - free_km_limit)

        extra_km_charged = extra_km * pricing_rule.price_per_extra_km

        final_price = (base_price + extra_km_charged) * pricing_rule.multiplier + pricing_rule.flat_fee

        return final_price, extra_km_charged

    def _create_damage(self, *, rental: Rental, damage_data: dict) -> Damage:
        required_fields = {"damage_type", "severity", "location", "description", "estimated_cost"}
        if not required_fields.issubset(damage_data.keys()):
            raise DamageRecordInvalidError()

        return Damage.objects.create(
            rental=rental,
            damage_type=damage_data["damage_type"],
            severity=damage_data["severity"],
            location=damage_data["location"],
            description=damage_data["description"],
            estimated_cost=damage_data["estimated_cost"],
            reported_at=timezone.now().date(),
        )