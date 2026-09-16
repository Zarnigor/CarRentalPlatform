from django.contrib.gis.db import models

from apps.fleet.enums import TransmissionType, FuelType, CarStatus
from apps.geo.models import Station


class CarModel(models.Model):
    brand = models.CharField(max_length=200)
    model = models.CharField(max_length=200)
    seats = models.IntegerField()
    transmission = models.CharField(max_length=20, choices=TransmissionType.choices, default=TransmissionType.MANUAL)
    fuel_type = models.CharField(max_length=20, choices=FuelType.choices, default=FuelType.PETROL)
    daily_base_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.brand} {self.model}"


class Car(models.Model):
    carModel = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    plate = models.CharField(max_length=20, unique=True)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=CarStatus.choices, default=CarStatus.AVAILABLE)
    current_location = models.PointField(srid=4326, geography=True)
    odometer_km = models.IntegerField()
    fuel_level = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return f"{self.plate}"

    class Meta:
        indexes = [
            models.Index(fields=['station'], name='car_station_fk'),
            models.Index(fields=['status']),
        ]

