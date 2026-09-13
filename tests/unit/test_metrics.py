from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus_metrics() -> None:
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/api/v1/health")
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "python_gc_objects_collected_total" in response.text
    assert "sgi_http_server_requests" in response.text
    assert "sgi_http_server_request_duration_ms" in response.text
