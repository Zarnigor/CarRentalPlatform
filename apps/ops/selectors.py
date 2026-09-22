from datetime import datetime

from django.db import connection

# Algo A10 — Fleet utilization via generate_series + LEFT JOIN
#
# generate_series splits the requested window into fixed-width buckets.
# A single LEFT JOIN on booking_rental covers every rental that overlaps
# each bucket; LEAST/GREATEST clamp the overlap to exactly the bucket edges.
# One query replaces the O(buckets × rentals) Python loop in services/ops.py,
# and FILTER (...) avoids counting non-overlapping rows in the SUM.


def get_utilization(
    *, date_from: datetime, date_to: datetime, granularity: str
) -> list[dict]:
    interval = "1 hour" if granularity == "hour" else "1 day"
    sql = """
    WITH
    buckets AS (
        SELECT
            gs                               AS bucket_start,
            gs + %(interval)s::interval      AS bucket_end
        FROM generate_series(
            %(from_ts)s::timestamptz,
            %(to_ts)s::timestamptz - %(interval)s::interval,
            %(interval)s::interval
        ) AS gs
    ),
    fleet AS (SELECT COUNT(*) AS n FROM fleet_car)
    SELECT
        b.bucket_start,
        b.bucket_end,
        f.n                                  AS total_cars,
        ROUND(
            COALESCE(
                SUM(
                    EXTRACT(EPOCH FROM (
                        LEAST(COALESCE(r.ended_at, NOW()), b.bucket_end)
                        - GREATEST(r.started_at, b.bucket_start)
                    )) / 3600.0
                ) FILTER (
                    WHERE
                        LEAST(COALESCE(r.ended_at, NOW()), b.bucket_end)
                        > GREATEST(r.started_at, b.bucket_start)
                ),
                0
            )::numeric,
            2
        )                                    AS busy_car_hours,
        ROUND(
            COALESCE(
                SUM(
                    EXTRACT(EPOCH FROM (
                        LEAST(COALESCE(r.ended_at, NOW()), b.bucket_end)
                        - GREATEST(r.started_at, b.bucket_start)
                    )) / 3600.0
                ) FILTER (
                    WHERE
                        LEAST(COALESCE(r.ended_at, NOW()), b.bucket_end)
                        > GREATEST(r.started_at, b.bucket_start)
                ),
                0
            )::numeric
            / NULLIF(
                f.n::numeric * EXTRACT(EPOCH FROM %(interval)s::interval) / 3600.0,
                0
            ) * 100,
            2
        )                                    AS utilization_pct
    FROM buckets b
    CROSS JOIN fleet f
    LEFT JOIN booking_rental r
        ON  r.started_at IS NOT NULL
        AND r.started_at  < b.bucket_end
        AND (r.ended_at IS NULL OR r.ended_at > b.bucket_start)
    GROUP BY b.bucket_start, b.bucket_end, f.n
    ORDER BY b.bucket_start
    """
    with connection.cursor() as cur:
        cur.execute(sql, {"from_ts": date_from, "to_ts": date_to, "interval": interval})
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
