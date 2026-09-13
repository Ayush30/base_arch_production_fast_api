from __future__ import annotations

from typing import Any

from opentelemetry import metrics

_http_requests_total: Any | None = None
_http_request_duration_ms: Any | None = None


def _http_instruments() -> tuple[Any, Any]:
    global _http_request_duration_ms, _http_requests_total

    if _http_requests_total is None or _http_request_duration_ms is None:
        meter = metrics.get_meter("app.http")
        _http_requests_total = meter.create_counter(
            "sgi_http_server_requests",
            unit="1",
            description="HTTP requests handled by the service.",
        )
        _http_request_duration_ms = meter.create_histogram(
            "sgi_http_server_request_duration_ms",
            unit="ms",
            description="HTTP request duration in milliseconds.",
        )

    return _http_requests_total, _http_request_duration_ms


def record_http_request(
    *,
    method: str,
    route: str,
    status_code: int,
    duration_ms: float,
) -> None:
    requests_total, request_duration_ms = _http_instruments()
    attributes = {
        "http.request.method": method,
        "http.route": route,
        "http.response.status_code": status_code,
    }

    requests_total.add(1, attributes)
    request_duration_ms.record(duration_ms, attributes)
