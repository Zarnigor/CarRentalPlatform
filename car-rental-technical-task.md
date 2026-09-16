servicelar
testlar (pytest bilan) - servicelarga
keyin har biriga MOdelViewset va generic viewset bilan apilarni yozish

# Technical Task — "AutoRent" Car Rental Platform

**Level:** Middle → Senior backend engineer
**Duration:** 4–6 weeks (part-time), split into 5 milestones
**Stack (mandatory):** Python 3.12, Django 5 + DRF, PostgreSQL 16 + PostGIS, GeoDjango, Redis 7, Celery, Docker / Docker Compose
**Optional stretch:** PgBouncer, Nginx, Prometheus + Grafana, Locust or k6, ClickHouse

The task has three layers on purpose:

1. **Product layer** — build a working service (the boring, necessary part).
2. **Algorithmic layer** — 10 isolated problems with complexity targets. Each one must be solved *twice*: naive version + optimized version, with a benchmark proving the difference.
3. **Systems layer** — throttling, capacity planning, concurrency correctness, horizontal scaling. Written analysis is a deliverable, not an afterthought.

Do not skip layer 3 write-ups. Half the value of this task is in the documents you produce, not the code.

---

## 1. Business domain

AutoRent operates a fleet of cars distributed across *stations* (parking lots) in several cities. Users:

- search for available cars near a location, for a time window;
- book a car (pickup station, optional different drop-off station = one-way rental);
- pay a deposit hold at booking, full charge at return;
- pick up / return the car, which produces a rental record with mileage, fuel, damage report.

Operations staff:

- manage fleet, stations, geofences (a car may not be dropped off outside a permitted polygon);
- rebalance cars between stations;
- monitor utilization and revenue.

### Non-functional targets (these are the acceptance bar)

| Metric | Target |
|---|---|
| Search endpoint p95 latency | ≤ 150 ms at 300 RPS |
| Booking creation p95 latency | ≤ 400 ms at 50 RPS |
| Double bookings under load | **exactly 0** |
| Availability (single AZ) | 99.9% |
| Cold-start deploy (docker compose up → healthy) | ≤ 90 s |
| Horizontal scale | 2× app replicas ⇒ ≥ 1.8× throughput, no code change |

---

## 2. Domain model

Design it yourself, but it must contain at least the following. Justify every index you create.

```
City         (id, name, timezone, boundary: MultiPolygonField)
Station      (id, city_fk, name, location: PointField, capacity, geofence: PolygonField)
CarModel     (id, brand, model, seats, transmission, fuel_type, daily_base_price)
Car          (id, car_model_fk, plate, station_fk, status, current_location: PointField,
              odometer_km, fuel_level)
Customer     (id, user_fk, license_no, license_verified_at, risk_score, tier)
Booking      (id, customer_fk, car_fk, pickup_station_fk, dropoff_station_fk,
              period: DateTimeRangeField, status, price_total, idempotency_key)
Rental       (id, booking_fk, started_at, ended_at, start_odometer, end_odometer, damages)
PricingRule  (id, scope, valid_period: DateTimeRangeField, priority, multiplier, flat_fee)
Payment      (id, booking_fk, provider_ref, kind, amount, status)
OutboxEvent  (id, aggregate_type, aggregate_id, event_type, payload, created_at, published_at)
```

**Hard requirements on the model:**

- `Booking.period` must be a `DateTimeRangeField`, **not** two separate columns. You will need range operators.
- A `btree_gist` exclusion constraint must make overlapping active bookings for the same car *physically impossible* at the DB level:

```sql
ALTER TABLE booking ADD CONSTRAINT booking_no_overlap
EXCLUDE USING gist (
    car_id WITH =,
    period WITH &&
) WHERE (status IN ('pending', 'confirmed', 'active'));
```

- `Station.location` and `Car.current_location` use SRID 4326; all distance math must use geography or a projected SRID — write down which you chose and why the other one is wrong for your case.
- Explain in `docs/model.md` why you did or did not denormalize `Car.station_fk` when the car is mid-rental.

---

## 3. API surface (DRF)

Minimum endpoints. All list endpoints paginated with **keyset pagination**, not offset — and you must explain why offset pagination degrades at page 5000.

```
POST   /api/v1/auth/token **(done)**
GET    /api/v1/cars/search?lat=&lon=&radius_m=&from=&to=&model=&sort=distance|price  **(done)**
GET    /api/v1/cars/{id}/availability?from=&to=    **(done)**
POST   /api/v1/bookings                (Idempotency-Key header REQUIRED)
GET    /api/v1/bookings/{id}      **(done)**
POST   /api/v1/bookings/{id}/cancel
POST   /api/v1/rentals/{id}/start
POST   /api/v1/rentals/{id}/finish
GET    /api/v1/stations/nearby?lat=&lon=&limit=
POST   /api/v1/ops/relocation-plan     (staff only)
GET    /api/v1/ops/utilization?from=&to=&granularity=hour|day
```

**Rules:**

- Every mutating endpoint accepts `Idempotency-Key`; replaying the same key returns the original response with `200` and header `Idempotency-Replayed: true`. Store keys in Redis with TTL 24h **and** in Postgres for durability — explain the trade-off.
- Errors follow RFC 9457 (`application/problem+json`).
- No business logic in serializers or views. Views → service layer → repository/manager. A view function longer than 15 lines is a review failure.

---

## 4. Algorithmic tasks

Each task lives in `algorithms/<name>/` with: `naive.py`, `optimized.py`, `bench.py`, `test_<name>.py`, and a `README.md` stating input size, measured times, and the complexity you claim. Benchmarks must run in CI.

### A1 — Fleet availability (interval overlap)

Given `N` cars and `M` bookings, return all cars free during `[start, end)`.

- Naive: O(N·M).
- Required: O((N + M) log M) in Python **and** a single SQL query using `tstzrange` + GiST index. Compare both against `EXPLAIN (ANALYZE, BUFFERS)`.
- Dataset: N = 20 000 cars, M = 3 000 000 bookings.
- Write down the point at which the Python version stops being viable and why.

### A2 — Peak concurrent demand (sweep line)

Given all bookings for a station over a period, compute the maximum number of simultaneously rented cars and the exact interval where that peak occurs.

- Required: O(M log M) sweep line over start/end events.
- Extension: return the top-`k` peak intervals, and the minimum fleet size needed to satisfy 95% of demand (this is a percentile over the concurrency step function — think carefully, it is *time-weighted*, not event-weighted).

### A3 — One-way rental rebalancing (min-cost assignment)

Stations have surplus and deficit of cars. Given a distance matrix, produce a relocation plan minimizing total driver-kilometres.

- Model it as a transportation problem / min-cost max-flow.
- Naive: greedy nearest-deficit. Required: Hungarian algorithm (square case) or SSP min-cost flow (general case).
- Compare total cost of greedy vs optimal on 50 stations. Report the gap as a percentage.
- Constraint to add in v2: each driver can chain at most 3 relocations — describe why this turns the problem NP-hard and what heuristic you would ship.

### A4 — Nearest available car (spatial k-NN)

Return the 20 nearest *available* cars to a point, filtered by time window and model.

Implement and benchmark **three** approaches:

1. `ST_DWithin` + `ORDER BY location <-> point` with a GiST index (KNN operator).
2. Geohash prefix bucketing in Postgres (precompute geohash column, B-tree index, expand neighbours).
3. Redis `GEOSEARCH` as a cache layer, with Postgres as source of truth.

Report p50/p95 for each at 300 RPS. Explain when the KNN index *cannot* be used (hint: what happens when you combine `ORDER BY <->` with a highly selective non-spatial filter?).

### A5 — Pricing engine (overlapping weighted intervals)

Pricing rules have validity ranges, scopes (global / city / model / car) and priority. A rental spanning 9 days may cross several rules.

- Split the rental period into maximal segments where the effective rule set is constant (line sweep), apply highest priority per segment, sum.
- Required: O(R log R) where R = number of applicable rules.
- Must be deterministic and unit-tested against a table of 30 fixture cases including: rules starting mid-day, equal priority ties, DST transition in `Asia/Tashkent`-style zones, and leap-second-adjacent timestamps.

### A6 — Rate limiter (the core of section 5)

Implement three limiters as reusable classes with identical interfaces:

1. **Fixed window counter** — show its burst flaw at window boundaries with a test that pushes 2× the limit through in 2 ms.
2. **Sliding window log** — exact, memory O(requests in window). Prove the memory cost with a measurement.
3. **Token bucket** — O(1) memory, allows configured burst. Implement as an **atomic Redis Lua script** (no `WATCH`/`MULTI` retry loops).

Requirements: single round-trip to Redis per check; clock skew across app replicas must not break it (use `TIME` from Redis, not the app clock); degrade *open* or *closed* on Redis failure — pick one, defend it in writing.

### A7 — Cache stampede protection

Search results are cached for 60 s. When a hot key expires, 300 concurrent requests hit Postgres simultaneously.

- Implement probabilistic early recomputation (XFetch) *and* a distributed-lock-based single-flight.
- Benchmark: measure DB queries per minute for a hot key under 300 RPS, before and after. Target: ≤ 1.2 DB queries per key per TTL.

### A8 — Fair task scheduling

A single Celery queue is shared by 200 corporate clients. One client submits 50 000 report jobs and starves everyone else.

- Design and implement weighted fair queuing on top of Redis (round-robin over per-tenant lists, or a deficit round robin scheduler).
- Prove fairness: with one tenant at 50 000 jobs and nine at 10 jobs, the nine tenants' jobs must all complete within 30 s.

### A9 — Geofence validation

Given a drop-off point and a set of permitted polygons (some with holes), decide fast whether the drop-off is legal.

- Naive: `ST_Contains` scan over all polygons.
- Required: bounding-box prefilter via GiST + `ST_Contains` refinement. Explain the filter/refine two-phase pattern in spatial indexes.
- Edge cases: point exactly on the boundary, polygon crossing the antimeridian, self-intersecting input polygon (must be rejected at write time with `ST_IsValid`).

### A10 — Utilization time series

Given 15M rental records, produce hourly utilization percentage per city for an arbitrary range.

- Naive: Python aggregation.
- Required: SQL with `generate_series` + `LEFT JOIN LATERAL`, plus a materialized view refreshed by Celery with concurrent refresh.
- Add a partial/covering index that turns the hot query into an index-only scan. Show the `EXPLAIN` before and after, including `Heap Fetches: 0`.

---

## 5. API throttling, RPS and QPS

This section produces **code + a written document** `docs/throttling.md`.

### 5.1 Definitions (write them out, in your own words)

- RPS vs QPS vs TPS — why the distinction matters when one API request fans out into 7 database queries and 2 Redis calls.
- Throughput vs concurrency vs latency, tied together by **Little's Law**: `L = λ × W`.
- Why p99 matters more than average, and why averaging p99s across replicas is statistically meaningless.

### 5.2 Tiered limits to implement

| Tier | Limit | Burst | Scope |
|---|---|---|---|
| Anonymous | 30 req/min | 10 | IP |
| Authenticated | 300 req/min | 50 | user id |
| Partner API | 3 000 req/min | 500 | api key |
| `POST /bookings` | 10 req/min | 3 | user id (separate bucket) |
| Search | 120 req/min | 30 | user id + coarse geohash |

Requirements:

- Custom DRF throttle class backed by the A6 token bucket, **not** `SimpleRateThrottle` (Django's default is a fixed-window counter with known burst issues — explain them).
- Response headers on every request: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`; on rejection `429` + `Retry-After`.
- A second layer at Nginx (`limit_req_zone`) as a cheap shield. Explain why app-level throttling alone is insufficient, and why Nginx-level alone is insufficient.
- Cost-based throttling: a search with `radius_m=50000` costs 5 tokens, `radius_m=1000` costs 1. Implement a cost function and document it.

### 5.3 Capacity planning exercise (pure math, no code)

Given:

- 400 000 monthly active users;
- each user makes 12 searches and 0.4 bookings per month;
- traffic follows a daily curve with peak-hour = 18% of daily volume, and peak-second = 3× the peak-hour average;
- search endpoint issues 3 SQL queries (p95 12 ms each) and 2 Redis calls (p95 0.4 ms);
- a Gunicorn sync worker handles one request at a time.

Compute and show your work:

1. Average RPS and peak RPS for search and for bookings.
2. Peak **QPS** hitting Postgres.
3. Required app concurrency at peak via Little's Law, at p95 latency of 150 ms.
4. Number of Gunicorn workers and replicas (state your worker class choice — sync vs gevent vs uvicorn — and why).
5. Postgres connection count required, then redo the number assuming PgBouncer in transaction mode. Explain which Django features break under transaction pooling (`DISABLE_SERVER_SIDE_CURSORS`, session-level advisory locks, `SET LOCAL` vs `SET`, prepared statements).
6. Redis ops/sec at peak, and whether one instance suffices.
7. The headroom factor you apply and why (hint: a system planned at 100% of peak is already down).

Deliver as a table with every intermediate number visible.

### 5.4 Load test

Write a Locust or k6 scenario that reproduces the mix above. Produce a report with:

- throughput vs latency curve, sweeping concurrency 10 → 1000;
- the **knee** of the curve — identify the saturated resource at that point (CPU? connections? GIL? disk?);
- error rate and 429 rate;
- a flame graph or `py-spy` profile of the app at saturation.

---

## 6. Easy scaling

Deliverable: `docs/scaling.md` + working `docker-compose.scale.yml`.

### 6.1 Statelessness

- No local file writes, no in-process caches that affect correctness, no sticky sessions.
- `docker compose up --scale api=4` must work with zero configuration change.
- Sessions and idempotency keys in Redis/Postgres only.

### 6.2 Database

- Read replica routing via a Django database router: search and reporting → replica, writes and read-your-writes flows → primary. Implement a `force_primary()` context manager and document exactly which endpoints need it.
- Handle replication lag: describe what a user sees if `POST /bookings` writes to primary and the immediate `GET /bookings/{id}` hits a lagging replica, and implement a fix.
- Partition `rental` by month (declarative partitioning). Show query plans proving partition pruning works for a date-ranged query.
- Connection pooling with PgBouncer; document `CONN_MAX_AGE` interaction (this is a classic trap — Django persistent connections + external pooler can silently multiply connections).

### 6.3 Caching layers

Document each layer, its TTL, its invalidation trigger, and its failure behaviour:

| Layer | Example | TTL | Invalidation |
|---|---|---|---|
| HTTP / CDN | station list | 5 min | version key |
| Redis application cache | search results | 60 s | write-through on booking |
| Materialized view | utilization | 15 min | Celery beat |
| Per-request memo | pricing rules | request | n/a |

Add a cache versioning scheme so a deploy never serves stale-shaped data.

### 6.4 Celery topology

- Separate queues: `default`, `payments`, `notifications`, `reports`, `geo`. Explain why a slow report job must never share a queue with payment capture.
- Configure per-queue concurrency, `acks_late=True`, `task_reject_on_worker_lost=True`, visibility timeout, and idempotent task bodies.
- Retry policy: exponential backoff **with jitter**. Explain the thundering-herd failure that plain exponential backoff causes.
- Beat schedules: fleet health check (5 min), stale booking expiry (1 min), materialized view refresh (15 min), relocation plan generation (nightly).

### 6.5 Scaling triggers

Define the concrete signal that tells you to add a replica of each component (app, Celery worker per queue, Postgres, Redis) — a metric with a threshold and a time window, not a vague statement. Also define the signal to scale *down*.

---

## 7. Systematic thinking tasks

These are written-analysis deliverables with supporting code.

### S1 — Prevent double booking, four ways

Implement all four, then write a comparison:

1. `SELECT ... FOR UPDATE` on the car row.
2. Postgres exclusion constraint (`btree_gist`) and catching `IntegrityError`.
3. Optimistic concurrency with a version column and retry.
4. Redis distributed lock.

For each: correctness under concurrency, behaviour under network partition, throughput cost, deadlock risk. **Which one do you ship, and which do you keep as a defence in depth?** Include the Redlock controversy in your reasoning — a Redis lock is not a correctness mechanism when the source of truth is Postgres.

**Proof required:** a test that fires 100 concurrent booking requests for the same car and the same window from 100 threads/processes and asserts exactly one `201` and 99 `409`.

### S2 — Transactional outbox

Booking confirmation must produce an event that a notification service consumes. Writing to Postgres and publishing to a broker are not atomic.

- Implement the outbox table + a Celery publisher with at-least-once delivery.
- Make the consumer idempotent.
- Write down why "write to DB, then publish in the same function" is broken, and enumerate the three failure interleavings.

### S3 — Saga for booking + payment hold

Booking creation must: reserve the car → place a deposit hold with the payment provider → confirm. The provider is a third party with 3 s p99 and occasional timeouts.

- Design compensating transactions for each step.
- Handle the ambiguous case: request timed out, but the hold *may* have succeeded. (Provider idempotency keys + reconciliation job.)
- Add a circuit breaker with defined open/half-open/closed thresholds.

### S4 — Failure mode analysis

Fill a table for at least 10 failures: Redis down, replica lag 30 s, Celery broker full, payment provider 500s, PostGIS query timeout, disk full, one AZ lost, deploy with a bad migration, clock skew between replicas, a hot tenant.

Columns: *Blast radius | Detection signal | Automatic mitigation | Manual runbook | Data-loss risk*.

### S5 — Migration under load

You must add a `NOT NULL` column with a default to `booking` (400M rows) with zero downtime.

- Write the multi-step plan (add nullable → backfill in batches → validate → set not null with `NOT VALID` + `VALIDATE CONSTRAINT`).
- Explain the lock each step takes and for how long.
- Explain why `ALTER TABLE ... ADD COLUMN ... DEFAULT` is safe on PG 11+ but the backfill still isn't free.

### S6 — Observability

- RED metrics (Rate, Errors, Duration) per endpoint, USE metrics (Utilization, Saturation, Errors) per resource.
- Structured JSON logs with a request id propagated into Celery tasks.
- Define 3 SLOs with error budgets, and one alert per SLO that pages a human. Explain why you did *not* alert on CPU.

---

## 8. Docker & delivery

- Multi-stage `Dockerfile`, non-root user, image ≤ 350 MB, no build toolchain in the final layer.
- `docker-compose.yml` (dev) and `docker-compose.scale.yml` (api ×4, worker ×3, Nginx, PgBouncer).
- Healthchecks: `/healthz` (liveness, no dependencies) and `/readyz` (readiness, checks DB + Redis). Explain why conflating them causes cascading restarts.
- Graceful shutdown: `SIGTERM` → stop accepting, drain in-flight, Celery `warm_shutdown`. Document your `stop_grace_period`.
- Makefile targets: `make up`, `make test`, `make bench`, `make load`, `make seed`.
- Seed command generating 20 000 cars, 200 stations, 3M bookings, 15M rentals with realistic geographic and temporal distribution (not uniform random — model rush hours and weekends).

---

## 9. Code quality bar

- Type hints on every public function; `mypy --strict` on the service layer.
- Google-style docstrings on all public classes and functions: purpose, args, returns, raises.
- `ruff` + `black` clean, enforced in CI.
- Test coverage ≥ 80% overall, 100% on pricing and availability logic.
- Tests split: `unit/` (no DB), `integration/` (DB + Redis), `load/`. Unit suite must run in < 10 s.

Reference style:

```python
def find_available_cars(
    station_ids: Sequence[int],
    period: DateTimeTZRange,
    *,
    car_model_id: int | None = None,
) -> list[Car]:
    """Return cars with no overlapping active booking in the given period.

    Uses a single query relying on the GiST index over ``booking.period``;
    the exclusion constraint guarantees the result cannot contain a car that
    is already booked, but callers must still re-check inside the booking
    transaction because availability is not held across requests.

    Args:
        station_ids: Stations to search within. Empty means all stations.
        period: Half-open rental interval ``[start, end)`` in UTC.
        car_model_id: Optional model filter.

    Returns:
        Cars ordered by station, then plate. Empty list if none available.

    Raises:
        ValueError: If ``period`` is unbounded or has zero length.
    """
```

---

## 10. Milestones

| # | Week | Content | Gate |
|---|---|---|---|
| M1 | 1 | Model, migrations, exclusion constraint, seed command, Docker up | 3M bookings seeded in < 10 min |
| M2 | 2 | Search + booking APIs, A1, A4, A5 | Search p95 ≤ 150 ms on seeded data |
| M3 | 3 | Throttling (A6, A7), capacity plan, load test report | Knee of the curve identified with evidence |
| M4 | 4 | Celery, outbox, saga, S1 concurrency proof | 100-thread test: exactly one 201 |
| M5 | 5–6 | Scaling: replicas, PgBouncer, partitioning, A2/A3/A8/A9/A10, all docs | `--scale api=4` gives ≥ 1.8× throughput |

---

## 11. Final deliverables checklist

- [ ] Running system via `docker compose up`
- [ ] `docs/model.md` — schema decisions, every index justified
- [ ] `docs/throttling.md` — limiter design + capacity math with worked numbers
- [ ] `docs/scaling.md` — layers, routing, triggers, cache table
- [ ] `docs/failure-modes.md` — S4 table
- [ ] `docs/adr/` — at least 6 Architecture Decision Records (context, options, decision, consequences)
- [ ] `algorithms/*/README.md` × 10 — with measured benchmarks
- [ ] Load test report with graphs and the identified bottleneck
- [ ] Concurrency proof test in CI
- [ ] Postmortem-style write-up of the single hardest bug you hit

---

## 12. Evaluation rubric (100 pts)

| Area | Pts | What earns full marks |
|---|---|---|
| Correctness under concurrency | 20 | Zero double bookings, proven by test, defence in depth explained |
| Algorithms | 20 | All 10 done, complexity claims backed by benchmarks |
| Throttling & capacity | 15 | Atomic limiter, correct math, load test finds the real bottleneck |
| Scaling | 15 | Genuinely stateless, replica routing with lag handling, partition pruning shown |
| Data modelling & SQL | 10 | Right index types, index-only scans, no N+1 |
| Code quality | 10 | Clean layering, typed, docstrings, fast tests |
| Written analysis | 10 | Trade-offs argued, not asserted; alternatives rejected with reasons |

**Automatic deductions:** business logic in views (−5); `SELECT *` in hot paths (−3); any `time.sleep` in tests (−3); a benchmark without a stated dataset size (−3); an ADR that lists only the chosen option (−5).

---

## 13. Stretch goals

- Replace polling with SSE/WebSocket for live car location, with an nginx heartbeat so proxies don't kill idle connections at 60 s.
- Debezium CDC from Postgres → Kafka → ClickHouse for the analytics endpoints; compare with the materialized view approach on the same query.
- Multi-tenant mode (`django-tenants`, schema per corporate client) and what it does to your connection math.
- Snowflake-style distributed ID generation for `booking.id` across three services, with disjoint node-bit ranges.
- Surge pricing driven by A2's real-time concurrency signal.
