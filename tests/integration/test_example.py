from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_example_item(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/examples", json={"name": "My Item"})
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["name"] == "My Item"
    assert data["version"] == 1

    item_id = data["id"]
    get_resp = await client.get(f"/api/v1/examples/{item_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == item_id


@pytest.mark.asyncio
async def test_list_example_items(client: AsyncClient) -> None:
    await client.post("/api/v1/examples", json={"name": "Item A"})
    await client.post("/api/v1/examples", json={"name": "Item B"})

    resp = await client.get("/api/v1/examples")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_delete_example_item(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/examples", json={"name": "Temp Item"})
    item_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/examples/{item_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/examples/{item_id}")
    assert get_resp.status_code == 404
