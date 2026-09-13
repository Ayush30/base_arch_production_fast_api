"""Run against the local seeded API; creates an order and simulates its payment."""

import argparse
import asyncio
from uuid import uuid4

import httpx


async def main(base_url: str) -> None:
    async with httpx.AsyncClient(base_url=base_url.rstrip("/") + "/api/v1", timeout=20) as client:
        login = await client.post(
            "/auth/login", json={"email": "buyer@example.com", "password": "Buyer-Demo-2026!"}
        )
        login.raise_for_status()
        client.headers["Authorization"] = "Bearer " + login.json()["access_token"]
        products = await client.get("/products", params={"currency": "USD"})
        products.raise_for_status()
        candidates = [p for p in products.json() if p["stock"] > 0]
        if not candidates:
            raise RuntimeError("No available USD products; run the local seed first")
        cart = await client.get("/cart")
        cart.raise_for_status()
        if cart.json():
            raise RuntimeError("Demo buyer cart is not empty; finish or clear it before this demo")
        addresses = await client.get("/addresses")
        addresses.raise_for_status()
        if not addresses.json():
            raise RuntimeError("No buyer address; run the local seed first")
        product = candidates[0]
        added = await client.put(f"/cart/items/{product['id']}", json={"quantity": 1})
        added.raise_for_status()
        result = await client.post(
            "/checkout",
            headers={"Idempotency-Key": str(uuid4())},
            json={
                "address_id": addresses.json()[0]["id"],
                "currency": "USD",
                "expected_total_minor": product["price_minor"],
            },
        )
        result.raise_for_status()
        order = result.json()
        paid = await client.post(f"/orders/{order['id']}/payments/local")
        paid.raise_for_status()
        print(
            f"Order {order['id']}: local payment simulated, total {order['total_minor']} USD cents"
        )
        print("Next: sign in as seller and use /seller/fulfillments in /docs.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    asyncio.run(main(parser.parse_args().base_url))
