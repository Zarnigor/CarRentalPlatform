# ===== Umumiy asos: apt paketlar faqat BIR MARTA o'rnatiladi =====
FROM python:3.12-slim AS base

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        libgdal36 \
        libgeos-c1v5 \
        libproj25 \
        curl

COPY --from=docker.io/astral/uv:0.12.9 /uv /uvx /bin/

WORKDIR /app


# ===== Faqat Python bog'liqliklar (pyproject/uv.lock o'zgarmasa — keshlanadi) =====
FROM base AS deps

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project


# ===== DEVELOPMENT: kod kerak emas — compose volume orqali mount qilinadi =====
FROM deps AS development

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# ===== BUILDER: faqat production uchun to'liq kodni qo'shib sync qilamiz =====
FROM deps AS builder

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ===== PRODUCTION =====
FROM base AS production

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

ENV PYTHONUNBUFFERED=1 \
    UV_NO_SYNC=1

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["gunicorn", "root.wsgi:application", "--bind", "0.0.0.0:8000"]