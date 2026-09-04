**POST   /api/v1/auth/token**

sequenceDiagram
    autonumber
    participant C as Client
    participant API as DRF View
    participant SVC as services.py (authenticate)
    participant DB@{ "type": "database", "alias": "Postgres (User)" }

    C->>API: POST /auth/token (username, password)
    API->>SVC: authenticate(username, password)
    SVC->>DB: SELECT user WHERE username=:username

    alt Foydalanuvchi topilmadi
        DB-->>SVC: empty
        SVC-->>API: invalid credentials
        API-->>C: 401 problem+json
    else Foydalanuvchi topildi
        DB-->>SVC: user row (password_hash)
        SVC->>SVC: check_password(password, password_hash)

        alt Parol mos kelmadi
            SVC-->>API: invalid credentials
            API-->>C: 401 problem+json
        else Parol to'g'ri
            SVC->>SVC: generate access_token (short TTL) + refresh_token (long TTL)
            SVC-->>API: tokens
            API-->>C: 200 OK (access_token, refresh_token)
        end
    end



**GET /cars/{id}/availability?from&to**

sequenceDiagram
    autonumber
    participant C as Client
    participant API as DRF View
    participant SEL as selectors.py(check_availability)
    participant DB@{ "type": "database", "alias": "Postgres (PostGIS)" }

    C->>API: GET /cars/{id}/availability?from&to
    API->>SEL: check_availability(car_id, from, to)
    SEL->>DB: SELECT 1 FROM booking WHERE car_id=:id AND period && tstzrange(:from,:to) AND status IN (pending, confirmed, active)

    alt Booking topildi (kesishuv bor)
        DB-->>SEL: rows exist
        SEL-->>API: available=false
        API-->>C: 200 OK { "available": false }
    else Booking topilmadi
        DB-->>SEL: empty
        SEL-->>API: available=true
        API-->>C: 200 OK { "available": true }
    end



**GET /cars/search?lat&lon&radius_m&from&to**

sequenceDiagram
    autonumber
    participant C@{ "type": "actor", "alias": "Client" }
    participant N@{ "type": "boundary", "alias": "Nginx" }
    participant API@{ "type": "boundary", "alias": "DRF View" }
    participant TH@{ "type": "control", "alias": "TokenBucket (Redis Lua)" }
    participant CACHE@{ "type": "database", "alias": "Redis Cache" }
    participant LOCK@{ "type": "control", "alias": "Redis Lock (single-flight)" }
    participant SEL@{ "type": "control", "alias": "selectors.py (search_cars)" }
    participant DB@{ "type": "database", "alias": "Postgres (PostGIS)" }

    C->>N: GET /cars/search?lat&lon&radius_m&from&to
    N->>N: limit_req_zone tekshiruvi
    N->>API: forward request

    API->>TH: check_and_consume(user_id+geohash, cost=f(radius_m))
    TH-->>API: allowed / retry_after

    alt Throttle limitidan oshgan (allowed=false)
        API-->>C: 429 Too Many Requests + RateLimit-* headers + Retry-After
    else Ruxsat berildi (allowed=true)
        API->>CACHE: GET search:{geohash}:{params_hash}

        alt Cache HIT va TTL muddati hali yetarli
            CACHE-->>API: cached result
            API-->>C: 200 OK (RateLimit-* headers)
        else Cache MISS (key umuman mavjud emas)
            API->>LOCK: SETNX lock:search:{key}
            alt Lock olindi
                API->>SEL: search_cars(lat, lon, radius_m, from, to, model)
                SEL->>DB: ST_DWithin + KNN (<->) + availability JOIN
                DB-->>SEL: rows
                SEL-->>API: car list
                API->>CACHE: SET search:{key} TTL=60s
                API->>LOCK: DEL lock:search:{key}
                API-->>C: 200 OK
            else Lock band (boshqa so'rov shu key uchun hisoblayapti)
                API->>CACHE: GET stale-if-error qiymatini o'qish
                CACHE-->>API: stale result (agar mavjud bo'lsa)
                API-->>C: 200 OK (stale-served)
            end
        else Cache mavjud, lekin XFetch ehtimoliy erta qayta hisoblash chegarasiga yetgan
   
            alt Lock olindi (early recompute)
                API->>SEL: search_cars(lat, lon, radius_m, from, to, model)
                SEL->>DB: ST_DWithin + KNN (<->) + availability JOIN
                DB-->>SEL: rows
                SEL-->>API: car list
                API->>CACHE: SET search:{key} TTL=60s (yangilangan)
                API->>LOCK: DEL lock:search:{key}
                API-->>C: 200 OK (fresh)
            else Lock band
                CACHE-->>API: joriy (hali tugamagan) cached qiymat
                API-->>C: 200 OK (eski, lekin hali valid)
            end
        end
    end


**GET /bookings/{id} (Authorization: Bearer token)**

sequenceDiagram
    autonumber
    participant C as Client
    participant API as DRF View
    participant SEL as selectors.py (get_booking_for_user)
    participant DB@{ "type": "database", "alias": "Postgres" }

    C->>API: GET /bookings/{id} (Authorization: Bearer token)
    API->>SEL: get_booking_for_user(booking_id, requesting_user)

    alt requesting_user.is_staff == true
        SEL->>DB: SELECT booking WHERE id=:id
    else requesting_user.is_staff == false
        SEL->>DB: SELECT booking WHERE id=:id AND customer.user_id=:requesting_user.id
    end

    DB-->>SEL: booking row (yoki bo'sh)

    alt Booking topilmadi (yoki egasi mos kelmadi)
        SEL-->>API: not found
        API-->>C: 404 problem+json
    else Booking topildi
        SEL-->>API: Booking object
        API-->>C: 200 OK
    end


**GET /stations/nearby?lat&lon&limit**

sequenceDiagram
    autonumber
    participant C as Client
    participant API as DRF View
    participant SEL as selectors.py (find_nearby_stations)
    participant DB@{ "type": "database", "alias": "Postgres (PostGIS)" }

    C->>API: GET /stations/nearby?lat&lon&limit
    API->>SEL: find_nearby_stations(lat, lon, limit)
    SEL->>DB: ORDER BY station.location <-> ST_MakePoint(:lon,:lat) LIMIT :limit
    DB-->>SEL: station rows
    SEL-->>API: station list
    API-->>C: 200 OK

**POST /bookings (car_id, period, card) - birinchi oddiysi **

sequenceDiagram
    autonumber
    participant C as Client
    participant API as DRF View
    participant SVC as BookingService
    participant DB as Postgres
    participant PAY as Payment Provider

    C->>API: POST /bookings (car_id, period, card)
    API->>SVC: create_booking(payload)
    SVC->>DB: BEGIN TRANSACTION
    SVC->>DB: INSERT booking (status='pending')
    DB-->>SVC: booking_id

    SVC->>PAY: place_hold(amount, booking_id)
    alt To'lov muvaffaqiyatli
        PAY-->>SVC: hold_id
        SVC->>DB: UPDATE booking SET status='confirmed', hold_id
        SVC->>DB: COMMIT
        SVC-->>API: booking (confirmed)
        API-->>C: 201 Created
    else To'lov rad etildi
        PAY-->>SVC: declined
        SVC->>DB: UPDATE booking SET status='failed'
        SVC->>DB: COMMIT
        SVC-->>API: error
        API-->>C: 402 Payment Required
    else Provayder javob bermadi (timeout / xatolik)
        PAY--xSVC: timeout yoki 500
        SVC->>DB: UPDATE booking SET status='failed'
        SVC->>DB: COMMIT
        SVC-->>API: error
        API-->>C: 502 Bad Gateway (qayta urinib ko'ring)
    end



**/bookings (car_id, period, amount) SAGA bilan**

sequenceDiagram
    autonumber
    participant C@{ "type": "actor", "alias": "Client" }
    participant API@{ "type": "boundary", "alias": "DRF View" }
    participant SAGA@{ "type": "control", "alias": "BookingSaga (orchestrator)" }
    participant DB@{ "type": "database", "alias": "Postgres" }
    participant CB@{ "type": "control", "alias": "Circuit Breaker" }
    participant PAY@{ "type": "boundary", "alias": "Payment Provider" }
    participant RECON@{ "type": "control", "alias": "Reconciliation Job (Celery, periodic)" }

    C->>API: POST /bookings (car_id, period, amount)
    API->>SAGA: create_booking_with_hold(payload)

    SAGA->>DB: BEGIN TRANSACTION
    SAGA->>DB: SELECT car FROM car WHERE id=:car_id FOR UPDATE
    DB-->>SAGA: car row (qulflangan)
    SAGA->>DB: INSERT INTO booking (car_id, period, status='reserved')
    DB-->>SAGA: booking_id
    SAGA->>DB: COMMIT

    SAGA->>CB: check_state()
    CB-->>SAGA: CLOSED / HALF-OPEN / OPEN

    alt Circuit OPEN (oxirgi N so'rovning ko'pchiligi xato bergan)
        SAGA->>DB: UPDATE booking SET status='cancelled' (car bo'shatildi)
        SAGA-->>API: 503 payment unavailable
        API-->>C: 503 + Retry-After
    else Circuit CLOSED yoki HALF-OPEN (so'rovga ruxsat bor)
        SAGA->>PAY: place_hold(amount, booking_id, idempotency_key=booking_id)

        alt Muvaffaqiyatli javob (p99 < 3s)
            PAY-->>SAGA: hold_id, status=ok
            SAGA->>CB: record_success()

            SAGA->>DB: UPDATE booking SET status='confirmed', hold_id=:hold_id
            SAGA-->>API: 201 Confirmed
            API-->>C: 201 Created

        else Provayder aniq rad etdi (masalan yetarli mablag' yo'q)
            PAY-->>SAGA: status=declined
            SAGA->>CB: record_success()
            SAGA->>DB: UPDATE booking SET status='cancelled'
            SAGA-->>API: 402 payment declined
            API-->>C: 402 Payment Required

        else Timeout (NOANIQ HOLAT — hold aslida o'tgan bo'lishi mumkin)
            PAY--xSAGA: timeout (3s dan oshdi, javob yo'q)
            SAGA->>CB: record_failure()
            SAGA->>DB: UPDATE booking SET status='payment_pending'
            SAGA-->>API: 202 Accepted
            API-->>C: 202 Accepted (pending, keyinroq status yangilanadi)

        else Provayder xatosi (5xx)
            PAY-->>SAGA: error 500/503
            SAGA->>CB: record_failure()
            SAGA->>DB: UPDATE booking SET status='cancelled'
            SAGA-->>API: 502 payment provider error
            API-->>C: 502 + Retry-After
        end
    end

    Note over RECON,PAY: === Reconciliation: faqat 'payment_pending' holatlar uchun, alohida vaqtda ===
    loop Har 30 soniyada (Celery periodic task)
        RECON->>DB: SELECT booking WHERE status='payment_pending' AND created_at < now()-30s
        DB-->>RECON: pending bookings

        loop Har bir pending booking uchun
            RECON->>PAY: query_hold_status(idempotency_key=booking_id)

            alt Hold aslida muvaffaqiyatli o'tgan ekan
                PAY-->>RECON: status=ok, hold_id
                RECON->>DB: UPDATE booking SET status='confirmed', hold_id=:hold_id
            else Hold aslida o'tmagan ekan
                PAY-->>RECON: status=not_found
                RECON->>DB: UPDATE booking SET status='cancelled'
            else Provayder hali ham javob bermayapti
                PAY--xRECON: timeout
                Note over RECON: Keyingi siklda qayta urinib ko'riladi<br/>(max N marta, keyin manual runbook'ga eskalatsiya)
            end
        end
    end



**POST /bookings/{id}/cancel**
sequenceDiagram
    autonumber
    participant C@{ "type": "actor", "alias": "Client" }
    participant API@{ "type": "boundary", "alias": "DRF View" }
    participant SVC@{ "type": "control", "alias": "services.py (cancel_booking)" }
    participant DB@{ "type": "database", "alias": "Postgres" }
    participant PAY@{ "type": "boundary", "alias": "Payment Provider" }
    participant OUT@{ "type": "database", "alias": "OutboxEvent (same TX)" }

    C->>API: POST /bookings/{id}/cancel
    API->>SVC: cancel_booking(booking_id, requesting_user)

    SVC->>DB: BEGIN TRANSACTION
    SVC->>DB: SELECT booking WHERE id=:id AND customer.user_id=:requesting_user.id FOR UPDATE
    DB-->>SVC: booking row (yoki bo'sh)

    alt Booking topilmadi (yoki egasi mos kelmadi)
        SVC->>DB: ROLLBACK
        SVC-->>API: not found
        API-->>C: 404 problem+json
    else Booking topildi

        alt status NOT IN (pending, confirmed)
            SVC->>DB: ROLLBACK
            SVC-->>API: already active/completed/cancelled
            API-->>C: 409 problem+json
        else status IN (pending, confirmed)

            alt Booking uchun hold qo'yilgan edi (hold_id mavjud)
                SVC->>PAY: release_hold(hold_id)
                PAY-->>SVC: released
            end

            SVC->>DB: UPDATE booking SET status='cancelled'
            SVC->>OUT: INSERT OutboxEvent(booking.cancelled) [bir TX ichida]
            SVC->>DB: COMMIT

            SVC-->>API: cancelled booking
            API-->>C: 200 OK
        end
    end



 **POST /rentals/{id}/start (odometer, fuel_level)**
sequenceDiagram
    autonumber
    participant C@{ "type": "actor", "alias": "Client (Staff/App)" }
    participant API@{ "type": "boundary", "alias": "DRF View" }
    participant SVC@{ "type": "control", "alias": "services.py (start_rental)" }
    participant DB@{ "type": "database", "alias": "Postgres" }

    C->>API: POST /rentals/{id}/start (odometer, fuel_level)
    API->>SVC: start_rental(booking_id, meta)

    SVC->>DB: BEGIN TRANSACTION
    SVC->>DB: SELECT booking WHERE id=:id FOR UPDATE

    alt Booking topilmadi yoki status != 'confirmed'
        SVC->>DB: ROLLBACK
        SVC-->>API: not found / wrong status
        API-->>C: 409 problem+json
    else Booking topildi va status='confirmed'
        SVC->>DB: UPDATE booking SET status='active'
        SVC->>DB: INSERT INTO rental (booking_id, started_at, start_odometer, start_fuel)
        DB-->>SVC: rental_id
        SVC->>DB: UPDATE car SET status='rented'
        SVC->>DB: COMMIT

        SVC-->>API: Rental object
        API-->>C: 201 Created
    end



**POST /rentals/{id}/finish (end_odometer, end_fuel, lat, lon, damages)**

sequenceDiagram
    autonumber
    participant C@{ "type": "actor", "alias": "Client (Staff/App)" }
    participant API@{ "type": "boundary", "alias": "DRF View" }
    participant SVC@{ "type": "control", "alias": "services.py (finish_rental)" }
    participant GEO@{ "type": "control", "alias": "selectors.py (validate_dropoff)" }
    participant PRICE@{ "type": "control", "alias": "selectors.py (calculate_final_price)" }
    participant DB@{ "type": "database", "alias": "Postgres" }
    participant PAY@{ "type": "boundary", "alias": "Payment Provider" }

    C->>API: POST /rentals/{id}/finish (end_odometer, end_fuel, lat, lon, damages)
    API->>SVC: finish_rental(rental_id, end_odometer, end_fuel, lat, lon, damages)

    SVC->>DB: SELECT rental JOIN booking WHERE rental.id=:id

    alt Rental topilmadi yoki status != 'active'
        SVC-->>API: not found / wrong status
        API-->>C: 409 problem+json
    else Rental topildi va status='active'
        SVC->>GEO: validate_dropoff(lat, lon, station.geofence)
        GEO->>DB: SELECT 1 WHERE ST_Contains(station.geofence, ST_MakePoint(:lon,:lat))<br/>WHERE bbox filter first (indeks)

        alt bbox tashqarisida (tez rad etish, ST_Contains chaqirilmaydi)
            DB-->>GEO: false
            GEO-->>SVC: invalid
            SVC-->>API: 422 Unprocessable
            API-->>C: problem+json (dropoff location invalid)
        else bbox ichida, aniq ST_Contains natijasi
            DB-->>GEO: true / false
            GEO-->>SVC: valid / invalid

            alt Geofence buzilgan (ST_Contains=false)
                SVC-->>API: 422 Unprocessable
                API-->>C: problem+json (dropoff location invalid)
            else Geofence to'g'ri
                SVC->>PRICE: calculate_final_price(rental, end_odometer, damages)
                PRICE->>DB: SELECT applicable PricingRule (base + km overage + damage fee)
                DB-->>PRICE: rules
                PRICE-->>SVC: final_amount

                SVC->>PAY: capture(hold_id, final_amount)

                alt Capture muvaffaqiyatli
                    PAY-->>SVC: charge_id

                    SVC->>DB: BEGIN TRANSACTION
                    SVC->>DB: UPDATE rental SET ended_at=now(), end_odometer, end_fuel, damages
                    SVC->>DB: UPDATE car SET status='available', current_location=ST_MakePoint(:lon,:lat)
                    SVC->>DB: UPDATE booking SET status='completed'
                    SVC->>DB: INSERT INTO payment (rental_id, kind='charge', amount=:final_amount, charge_id)
                    SVC->>DB: COMMIT

                    SVC-->>API: Rental finished + invoice
                    API-->>C: 200 OK

                else Capture muvaffaqiyatsiz (masalan karta bloklangan)
                    PAY-->>SVC: error
                    SVC->>DB: BEGIN TRANSACTION
                    SVC->>DB: UPDATE rental SET ended_at=now(), end_odometer, end_fuel, damages
                    SVC->>DB: UPDATE car SET status='available', current_location=ST_MakePoint(:lon,:lat)
                    SVC->>DB: UPDATE booking SET status='payment_failed'
                    SVC->>DB: COMMIT
                    Note over SVC,DB: Mashina baribir bo'shatiladi (jismonan qaytarilgan),<br/>lekin to'lov staff tomonidan qo'lda hal qilinishi kerak

                    SVC-->>API: capture failed, manual review required
                    API-->>C: 402 problem+json
                end
            end
        end
    end



