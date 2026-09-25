import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("booking", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Rental",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("started_at", models.DateTimeField(null=True)),
                ("ended_at", models.DateTimeField(null=True)),
                ("start_odometer", models.DecimalField(decimal_places=2, max_digits=10)),
                ("end_odometer", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("completed", "Completed"),
                            ("disputed", "Disputed"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "final_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "extra_km_charged",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "booking",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rentals",
                        to="booking.booking",
                    ),
                ),
            ],
        ),
    ]
