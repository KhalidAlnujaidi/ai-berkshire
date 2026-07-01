"""Prometheus metrics middleware for FastAPI.

Exposes a /metrics endpoint compatible with Prometheus/Grafana.
Tracks:
  - HTTP request count by method/path/status
  - HTTP request latency histogram by path
  - In-flight requests gauge

Fail-soft: if prometheus_client is not installed, metrics are silently
disabled and /metrics returns a 503 with a helpful message.
"""

import time
import logging
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, generate_latest,
        CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed — /metrics disabled")

# ── Metrics definitions ──────────────────────────────────────────────────────

if PROMETHEUS_AVAILABLE:
    http_requests_total = Counter(
        "mizan_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
        registry=REGISTRY,
    )

    http_request_duration_seconds = Histogram(
        "mizan_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "path"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=REGISTRY,
    )

    http_requests_in_flight = Gauge(
        "mizan_http_requests_in_flight",
        "Number of HTTP requests currently being processed",
        registry=REGISTRY,
    )

    # Business metrics
    sharia_screenings_total = Counter(
        "mizan_sharia_screenings_total",
        "Total Sharia compliance screenings performed",
        ["verdict"],
        registry=REGISTRY,
    )

    stocks_price_fetches_total = Counter(
        "mizan_stock_price_fetches_total",
        "Total live stock price fetches",
        ["source", "status"],
        registry=REGISTRY,
    )

    active_users_gauge = Gauge(
        "mizan_active_users",
        "Number of registered users (gauge updated periodically)",
        registry=REGISTRY,
    )

    watchlist_items_gauge = Gauge(
        "mizan_watchlist_items",
        "Total watchlist items across all users",
        registry=REGISTRY,
    )


def _normalize_path(path: str) -> str:
    """Normalize paths to reduce cardinality.

    /api/stocks/1120 -> /api/stocks/:ticker
    /api/watchlist/2222 -> /api/watchlist/:ticker
    """
    parts = path.strip("/").split("/")
    if len(parts) >= 3 and parts[0] == "api":
        # /api/stocks/{ticker} -> /api/stocks/:ticker
        if parts[1] in ("stocks", "watchlist") and len(parts) == 3:
            return f"/api/{parts[1]}/:ticker"
        # /api/stocks/{ticker}/price -> /api/stocks/:ticker/price
        if parts[1] == "stocks" and len(parts) == 4:
            return f"/api/stocks/:ticker/{parts[3]}"
    return path


async def metrics_middleware(request: Request, call_next):
    """FastAPI middleware that records Prometheus metrics for each request."""
    if not PROMETHEUS_AVAILABLE:
        return await call_next(request)

    # Skip metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)

    http_requests_in_flight.inc()
    start = time.perf_counter()

    try:
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        path = _normalize_path(request.url.path)
        method = request.method
        status = str(response.status_code)

        http_requests_total.labels(method=method, path=path, status=status).inc()
        http_request_duration_seconds.labels(method=method, path=path).observe(elapsed)

        return response
    finally:
        http_requests_in_flight.dec()


async def metrics_endpoint(request: Request):
    """Prometheus /metrics endpoint.

    Returns metrics in Prometheus exposition format.
    """
    if not PROMETHEUS_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"detail": "prometheus_client not installed. Run: pip install prometheus_client"},
        )
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
