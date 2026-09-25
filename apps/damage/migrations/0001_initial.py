import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("rental", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Damage",
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
                (
                    "damage_type",
                    models.CharField(
                        choices=[
                            ("SCRATCH", "scratch"),
                            ("DENT", "dent"),
                            ("CRACK", "crack"),
                            ("BROKEN", "broken"),
                            ("STAINED", "stained"),
                            ("MISSING_PART", "missing_part"),
                            ("MECHANICAL", "mechanical"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("MINOR", "minor"),
                            ("MODERATE", "moderate"),
                            ("SEVERE", "severe"),
                        ],
                        max_length=20,
                    ),
                ),
                ("location", models.CharField(max_length=20)),
                ("description", models.TextField()),
                (
                    "estimated_cost",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("reported_at", models.DateField()),
                ("resolved_at", models.DateTimeField(auto_now_add=True)),
                (
                    "rental",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="rental.rental",
                    ),
                ),
            ],
        ),
    ]
