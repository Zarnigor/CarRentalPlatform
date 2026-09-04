from psycopg2.extras import DateTimeTZRange

def check_availability(car_id: int, period_from: datetime, period_to: datetime) -> bool:
    has_conflict = Booking.objects.filter(
        car_id=car_id,
        status__in=ACTIVE_BOOKING_STATUSES,
        period__overlap=DateTimeTZRange(period_from, period_to),
    ).exists()
    return not has_conflict