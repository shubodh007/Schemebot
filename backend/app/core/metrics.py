from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
from starlette.responses import PlainTextResponse

llm_requests = Counter(
    "llm_requests_total",
    "Total LLM requests",
    labelnames=["provider", "model", "status"],
)

llm_duration = Histogram(
    "llm_request_duration_seconds",
    "LLM request latency",
    labelnames=["provider", "model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

cache_hits = Counter(
    "cache_hits_total",
    "Cache hit count",
    labelnames=["cache_type"],
)

cache_misses = Counter(
    "cache_misses_total",
    "Cache miss count",
    labelnames=["cache_type"],
)

circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    labelnames=["provider"],
)

http_requests = Counter(
    "http_requests_total",
    "HTTP requests",
    labelnames=["method", "endpoint", "status"],
)

http_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    labelnames=["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query latency",
    labelnames=["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)

metrics_router = APIRouter(tags=["monitoring"])


@metrics_router.get("/metrics")
async def metrics() -> Response:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
