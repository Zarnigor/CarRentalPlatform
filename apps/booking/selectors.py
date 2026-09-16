from psycopg2.extras import DateTimeTZRange
from apps.booking.models import Booking
from apps.booking.enums import BookingStatus


class BookingSelector:
    def check_availability(self, *, car_id: int, period: DateTimeTZRange) -> bool:
        overlapping_exists = Booking.objects.filter(
            car_id=car_id,
            period__overlap=period,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        ).exists()

        return not overlapping_exists

    def get_booking(self, *, booking_id: int) -> Booking:
        from apps.booking.exceptions import BookingNotFoundError
        try:
            return Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            raise BookingNotFoundError(booking_id=booking_id)
