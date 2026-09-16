from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from apps.booking.models import Rental
from apps.fleet.models import Car


class OpsService:
    def get_utilization(
        self, *,
        date_from: datetime,
        date_to: datetime,
        granularity: str,  # "hour" yoki "day"
    ) -> list[dict]:
        """
        Har bir vaqt bo'lagi (soat/kun) uchun flot band bo'lish foizini hisoblaydi.
        """
        total_cars = Car.objects.count()
        if total_cars == 0:
            return []

        bucket_size = timedelta(hours=1) if granularity == "hour" else timedelta(days=1)

        # Berilgan oraliqqa tegishli barcha rentallarni bitta so'rov bilan olamiz
        # shunda faqat bir marta dbga murojat qilinadi

        rentals = Rental.objects.filter(
            Q(started_at__lt=date_to) & (Q(ended_at__gt=date_from) | Q(ended_at__isnull=True)),
        ).exclude(started_at__isnull=True)

        results = []
        bucket_start = date_from

        while bucket_start < date_to:
            bucket_end = min(bucket_start + bucket_size, date_to)
            bucket_duration_hours = (bucket_end - bucket_start).total_seconds() / 3600

            busy_car_hours = Decimal("0")

            for rental in rentals:
                rental_start = rental.started_at
                rental_end = rental.ended_at or timezone.now()

                overlap_start = max(rental_start, bucket_start)
                overlap_end = min(rental_end, bucket_end)

                if overlap_start < overlap_end:
                    overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600
                    busy_car_hours += Decimal(str(overlap_hours))

            available_car_hours = Decimal(str(total_cars * bucket_duration_hours))
            utilization_pct = (
                (busy_car_hours / available_car_hours * 100)
                if available_car_hours > 0 else Decimal("0")
            )

            results.append({
                "period_start": bucket_start,
                "period_end": bucket_end,
                "utilization_pct": round(utilization_pct, 2),
                "busy_car_hours": round(busy_car_hours, 2),
                "total_cars": total_cars,
            })

            bucket_start = bucket_end

        return results