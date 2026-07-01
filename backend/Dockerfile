# ──────────────────────────────────────────────────────────────────────────────
# Mizan API — Production Dockerfile
# Multi-stage build, non-root user, health check
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps for psycopg2 (libpq-dev) and bcrypt (gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime deps: libpq5 for psycopg2, curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app.py auth.py database.py models.py schemas.py stocks.json ./
COPY sharia_screener.py ./sharia_screener.py

# ── Non-root user for security ──────────────────────────────────────────────
RUN groupadd -r -g 10001 mizan && useradd -r -u 10001 -g mizan -s /bin/bash mizan \
    && chown -R mizan:mizan /app
RUN mkdir -p /tmp && chown mizan:mizan /tmp
USER mizan

# ── Environment ─────────────────────────────────────────────────────────────
ENV APP_ENV=production
ENV PORT=8000
EXPOSE 8000

# ── Health check ────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# ── Production server: Gunicorn with Uvicorn workers ────────────────────────
# Uses $WEB_CONCURRENCY workers (default 2), auto-tuned to CPU count.
CMD ["sh", "-c", \
    "gunicorn app:app \
     --bind 0.0.0.0:${PORT} \
     --workers ${WEB_CONCURRENCY:-2} \
     --worker-class uvicorn.workers.UvicornWorker \
     --timeout 120 \
     --keep-alive 5 \
     --access-logfile - \
     --error-logfile -"]
