import django.contrib.postgres.constraints
import django.db.models
from django.db import migrations


class Migration(migrations.Migration):
    """
    The original constraint used lowercase status values ('pending', 'confirmed')
    which never matched the stored uppercase enum values ('PENDING', 'CONFIRMED').
    This migration drops the broken constraint and recreates it correctly.
    """

    dependencies = [
        ("booking", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="booking",
            name="exclude_overlapping_bookings",
        ),
        migrations.AddConstraint(
            model_name="booking",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                condition=django.db.models.Q(
                    ("status__in", ["PENDING", "CONFIRMED", "ACTIVE"])
                ),
                expressions=[("car", "="), ("period", "&&")],
                name="exclude_overlapping_bookings",
            ),
        ),
    ]
