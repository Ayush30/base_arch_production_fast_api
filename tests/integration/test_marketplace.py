"""Exercise actual HTTP auth and separate PostgreSQL transactions, including races."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.events.models import OutboxEvent
from app.domains.finance.models import LedgerEntry, Payment
from app.domains.orders.models import Order, OrderItem

ADDRESS = {
    "recipient": "Buyer",
    "line1": "1 Test Street",
    "city": "Test",
    "region": "CA",
    "postal_code": "90001",
    "country_code": "US",
}


async def product(
    client: AsyncClient,
    accounts: dict,
    seller: str = "seller",
    stock: int = 10,
    currency: str = "USD",
) -> dict:
    response = await client.post(
        "/api/v1/seller/products",
        headers=accounts[seller]["headers"],
        json={
            "sku": uuid4().hex,
            "name": "Backpack",
            "category": "Bags",
            "price_minor": 1999,
            "currency": currency,
            "stock": stock,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def prepare(
    client: AsyncClient, accounts: dict, products: list[dict], buyer: str = "buyer"
) -> dict:
    headers = accounts[buyer]["headers"]
    address = await client.post("/api/v1/addresses", headers=headers, json=ADDRESS)
    assert address.status_code == 201, address.text
    for item in products:
        response = await client.put(
            f"/api/v1/cart/items/{item['id']}", headers=headers, json={"quantity": 1}
        )
        assert response.status_code == 200, response.text
    return {
        "address_id": address.json()["id"],
        "currency": "USD",
        "expected_total_minor": sum(p["price_minor"] for p in products),
    }


async def checkout(
    client: AsyncClient, accounts: dict, body: dict, buyer: str = "buyer", key: str | None = None
) -> Response:
    return await client.post(
        "/api/v1/checkout",
        headers={**accounts[buyer]["headers"], "Idempotency-Key": key or uuid4().hex},
        json=body,
    )


async def deliver(client: AsyncClient, accounts: dict, order: dict) -> None:
    for line in order["items"]:
        seller = "seller" if line["seller_id"] == accounts["seller"]["id"] else "seller2"
        for status in ("shipped", "delivered"):
            response = await client.post(
                f"/api/v1/seller/fulfillments/{line['id']}",
                headers=accounts[seller]["headers"],
                json={"status": status, "tracking_number": "TRACK-123"},
            )
            assert response.status_code == 200, response.text


async def test_full_marketplace_lifecycle(
    client: AsyncClient, accounts: dict, db_session: AsyncSession
) -> None:
    products = [await product(client, accounts), await product(client, accounts, "seller2")]
    body = await prepare(client, accounts, products)
    response = await checkout(client, accounts, body, key="mobile-checkout-001")
    assert response.status_code == 201, response.text
    order = response.json()
    assert order["total_minor"] == 3998 and len(order["items"]) == 2
    retry = await checkout(client, accounts, body, key="mobile-checkout-001")
    assert retry.json()["id"] == order["id"]
    assert (await client.get("/api/v1/cart", headers=accounts["buyer"]["headers"])).json() == []
    changed = await checkout(
        client, accounts, {**body, "expected_total_minor": 123}, key="mobile-checkout-001"
    )
    assert changed.status_code == 409
    pay_url = f"/api/v1/orders/{order['id']}/payments/local"
    paid = await client.post(pay_url, headers=accounts["buyer"]["headers"])
    assert paid.status_code == 200, paid.text
    assert (await client.post(pay_url, headers=accounts["buyer"]["headers"])).json()[
        "id"
    ] == paid.json()["id"]
    assert (await db_session.scalar(select(func.count(Payment.id)))) == 1
    for seller in ("seller", "seller2"):
        fulfillment = await client.get(
            "/api/v1/seller/fulfillments", headers=accounts[seller]["headers"]
        )
        assert len(fulfillment.json()) == 1
        assert fulfillment.json()[0]["item"]["seller_id"] == accounts[seller]["id"]
    await deliver(client, accounts, order)
    review = await client.post(
        f"/api/v1/products/{products[0]['id']}/reviews",
        headers=accounts["buyer"]["headers"],
        json={"rating": 5},
    )
    assert review.status_code == 201, review.text
    assert (
        await client.post(
            f"/api/v1/products/{products[0]['id']}/reviews",
            headers=accounts["buyer"]["headers"],
            json={"rating": 4},
        )
    ).status_code == 409
    assert (await client.get(f"/api/v1/products/{products[0]['id']}/reviews")).json()[0][
        "rating"
    ] == 5
    report = await client.get("/api/v1/analytics/sales", headers=accounts["analytics"]["headers"])
    assert report.json() == [
        {"currency": "USD", "paid_orders": 1, "gross_minor": 3998, "commission_minor": 400}
    ]
    for path in (
        "/analytics/products",
        "/analytics/sellers",
        "/seller/sales",
        "/orders",
        "/addresses",
        "/seller/products",
    ):
        role = (
            "analytics"
            if path.startswith("/analytics")
            else "seller"
            if path.startswith("/seller")
            else "buyer"
        )
        assert (
            await client.get("/api/v1" + path, headers=accounts[role]["headers"])
        ).status_code == 200
    requested = await client.post(
        f"/api/v1/orders/{order['id']}/returns",
        headers=accounts["buyer"]["headers"],
        json={"reason": "Wrong size received"},
    )
    assert requested.status_code == 201, requested.text
    refund_url = f"/api/v1/finance/orders/{order['id']}/refund/local"
    assert (
        await client.post(
            refund_url,
            headers=accounts["finance"]["headers"],
            json={"goods_received": False, "reason": "Goods inspected"},
        )
    ).status_code == 400
    refunded = await client.post(
        refund_url,
        headers=accounts["finance"]["headers"],
        json={"goods_received": True, "reason": "Goods inspected"},
    )
    assert refunded.status_code == 200 and refunded.json()["status"] == "refunded", refunded.text
    assert (
        await client.post(
            refund_url,
            headers=accounts["finance"]["headers"],
            json={"goods_received": True, "reason": "Goods inspected"},
        )
    ).status_code == 200
    assert await db_session.scalar(select(func.sum(LedgerEntry.amount_minor))) == 0
    assert (
        await client.get("/api/v1/analytics/sales", headers=accounts["analytics"]["headers"])
    ).json() == []
    for p in products:
        assert (await client.get(f"/api/v1/products/{p['id']}")).json()["stock"] == 10
    assert await db_session.scalar(select(func.count(OutboxEvent.id))) > 0
    for path, role in (
        ("/finance/payments", "finance"),
        ("/finance/returns", "finance"),
        ("/finance/ledger", "finance"),
        ("/finance/settlements", "finance"),
        ("/seller/settlements", "seller"),
        ("/returns", "buyer"),
        ("/admin/audit", "admin"),
        ("/admin/users", "admin"),
    ):
        assert (
            await client.get("/api/v1" + path, headers=accounts[role]["headers"])
        ).status_code == 200


async def test_checkout_race_never_oversells(client: AsyncClient, accounts: dict) -> None:
    p = await product(client, accounts, stock=1)
    bodies = [await prepare(client, accounts, [p], buyer) for buyer in ("buyer", "buyer2")]
    results = await asyncio.gather(
        *(
            checkout(client, accounts, body, buyer)
            for body, buyer in zip(bodies, ("buyer", "buyer2"), strict=True)
        )
    )
    assert sorted(r.status_code for r in results) == [201, 409]
    assert (await client.get(f"/api/v1/products/{p['id']}")).json()["stock"] == 0


async def test_simultaneous_duplicate_checkout(client: AsyncClient, accounts: dict) -> None:
    p = await product(client, accounts)
    body = await prepare(client, accounts, [p])
    responses = await asyncio.gather(
        *(checkout(client, accounts, body, key="same-mobile-retry") for _ in range(2))
    )
    assert [r.status_code for r in responses] == [201, 201]
    assert responses[0].json()["id"] == responses[1].json()["id"]
    assert (await client.get(f"/api/v1/products/{p['id']}")).json()["stock"] == 9


async def test_checkout_rollback_and_cancellation(
    client: AsyncClient, accounts: dict, db_session: AsyncSession
) -> None:
    p = await product(client, accounts)
    body = await prepare(client, accounts, [p])
    wrong = await checkout(client, accounts, {**body, "expected_total_minor": 1})
    assert wrong.status_code == 409
    assert (await client.get(f"/api/v1/products/{p['id']}")).json()["stock"] == 10
    assert await db_session.scalar(select(func.count(Order.id))) == 0
    response = await checkout(client, accounts, body)
    order = response.json()
    url = f"/api/v1/orders/{order['id']}/cancel"
    for _ in range(2):
        assert (await client.post(url, headers=accounts["buyer"]["headers"])).status_code == 200
    assert (await client.get(f"/api/v1/products/{p['id']}")).json()["stock"] == 10
    assert (
        await client.post(
            f"/api/v1/orders/{order['id']}/payments/local", headers=accounts["buyer"]["headers"]
        )
    ).status_code == 409


async def test_ownership_and_role_boundaries(client: AsyncClient, accounts: dict) -> None:
    p = await product(client, accounts)
    assert (
        await client.patch(
            f"/api/v1/seller/products/{p['id']}",
            headers=accounts["seller2"]["headers"],
            json={"version": 1, "stock": 99},
        )
    ).status_code == 403
    for path, role in (
        ("/finance/payments", "buyer"),
        ("/admin/users", "finance"),
        ("/analytics/sales", "seller"),
        ("/orders", "analytics"),
        ("/seller/products", "buyer"),
    ):
        assert (
            await client.get("/api/v1" + path, headers=accounts[role]["headers"])
        ).status_code == 403
    assert (await client.get("/api/v1/orders")).status_code == 401
    assert (
        await client.get("/api/v1/orders", headers={"Authorization": "Bearer invalid"})
    ).status_code == 401
    body = await prepare(client, accounts, [p])
    assert (await checkout(client, accounts, body, "buyer2")).status_code == 404
    order = (await checkout(client, accounts, body)).json()
    for suffix in ("", "/cancel", "/payments/local"):
        method = client.get if not suffix else client.post
        assert (
            await method(
                f"/api/v1/orders/{order['id']}" + suffix, headers=accounts["buyer2"]["headers"]
            )
        ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/seller/fulfillments/{order['items'][0]['id']}",
            headers=accounts["seller2"]["headers"],
            json={"status": "shipped", "tracking_number": "track"},
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/products/{p['id']}/reviews",
            headers=accounts["buyer2"]["headers"],
            json={"rating": 5},
        )
    ).status_code == 403


async def test_catalog_versions_moderation_and_validation(
    client: AsyncClient, accounts: dict
) -> None:
    p = await product(client, accounts)
    url = f"/api/v1/seller/products/{p['id']}"
    assert (
        await client.patch(
            url, headers=accounts["seller"]["headers"], json={"version": 1, "stock": 20}
        )
    ).json()["version"] == 2
    assert (
        await client.patch(
            url, headers=accounts["seller"]["headers"], json={"version": 1, "stock": 30}
        )
    ).status_code == 409
    assert (
        await client.patch(
            url, headers=accounts["seller"]["headers"], json={"version": 2, "stock": -1}
        )
    ).status_code == 422
    assert (await client.get("/api/v1/products?limit=101")).status_code == 422
    assert (
        len((await client.get("/api/v1/products?search=Back&category=Bags&currency=USD")).json())
        == 1
    )
    blocked = await client.post(
        f"/api/v1/admin/products/{p['id']}/moderation",
        headers=accounts["admin"]["headers"],
        json={"blocked": True, "reason": "Awaiting product verification"},
    )
    assert blocked.status_code == 200
    assert (await client.get(f"/api/v1/products/{p['id']}")).status_code == 404
    assert (await client.get("/api/v1/products")).json() == []
    assert (
        await client.put(
            f"/api/v1/cart/items/{p['id']}",
            headers=accounts["buyer"]["headers"],
            json={"quantity": 1},
        )
    ).status_code == 404


async def test_settlement_waits_for_return_window(
    client: AsyncClient, accounts: dict, db_session: AsyncSession
) -> None:
    p = await product(client, accounts)
    order = (await checkout(client, accounts, await prepare(client, accounts, [p]))).json()
    await client.post(
        f"/api/v1/orders/{order['id']}/payments/local", headers=accounts["buyer"]["headers"]
    )
    await deliver(client, accounts, order)
    url = f"/api/v1/finance/orders/{order['id']}/settlements"
    body = {"seller_id": accounts["seller"]["id"], "external_reference": "bank-transfer-001"}
    assert (
        await client.post(url, headers=accounts["finance"]["headers"], json=body)
    ).status_code == 409
    line = await db_session.get(OrderItem, UUID(order["items"][0]["id"]))
    line.delivered_at = datetime.now(UTC) - timedelta(days=15)
    await db_session.commit()
    response = await client.post(url, headers=accounts["finance"]["headers"], json=body)
    assert response.status_code == 201, response.text
    assert response.json()["net_minor"] == 1799
    assert (await client.post(url, headers=accounts["finance"]["headers"], json=body)).json()[
        "id"
    ] == response.json()["id"]
    assert (
        await client.post(
            url,
            headers=accounts["finance"]["headers"],
            json={**body, "external_reference": "other-transfer-001"},
        )
    ).status_code == 409
    assert (
        await client.post(
            f"/api/v1/orders/{order['id']}/returns",
            headers=accounts["buyer"]["headers"],
            json={"reason": "Too late return"},
        )
    ).status_code == 409


async def test_currency_expansion_and_mixed_cart_rollback(
    client: AsyncClient, accounts: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    unsupported = await client.post(
        "/api/v1/seller/products",
        headers=accounts["seller"]["headers"],
        json={
            "sku": "eur",
            "name": "Euro product",
            "category": "Bags",
            "price_minor": 1999,
            "currency": "EUR",
            "stock": 10,
        },
    )
    assert unsupported.status_code == 400
    monkeypatch.setattr(settings, "supported_currencies", ["USD", "EUR"])
    usd = await product(client, accounts)
    eur = await product(client, accounts, currency="EUR")
    body = await prepare(client, accounts, [usd, eur])
    assert (await checkout(client, accounts, body)).status_code == 400
    for item in (usd, eur):
        assert (await client.get(f"/api/v1/products/{item['id']}")).json()["stock"] == 10
    assert (
        await client.delete(f"/api/v1/cart/items/{usd['id']}", headers=accounts["buyer"]["headers"])
    ).status_code == 204
    body.update(currency="EUR", expected_total_minor=1999)
    order = (await checkout(client, accounts, body)).json()
    assert order["currency"] == "EUR"
    assert (
        await client.post(
            f"/api/v1/orders/{order['id']}/payments/local", headers=accounts["buyer"]["headers"]
        )
    ).status_code == 200
    report = (
        await client.get("/api/v1/analytics/sales", headers=accounts["analytics"]["headers"])
    ).json()
    assert report == [
        {"currency": "EUR", "paid_orders": 1, "gross_minor": 1999, "commission_minor": 200}
    ]


async def test_cart_address_and_fulfillment_guards(client: AsyncClient, accounts: dict) -> None:
    p = await product(client, accounts, stock=2)
    headers = accounts["buyer"]["headers"]
    assert (
        await client.put(f"/api/v1/cart/items/{p['id']}", headers=headers, json={"quantity": 3})
    ).status_code == 400
    body = await prepare(client, accounts, [p])
    assert (
        await client.put(f"/api/v1/cart/items/{p['id']}", headers=headers, json={"quantity": 2})
    ).json()["quantity"] == 2
    assert (
        await client.put(f"/api/v1/cart/items/{p['id']}", headers=headers, json={"quantity": 1})
    ).status_code == 200
    order = (await checkout(client, accounts, body)).json()
    item_url = f"/api/v1/seller/fulfillments/{order['items'][0]['id']}"
    ship = {"status": "shipped", "tracking_number": "TRACK-1"}
    assert (
        await client.post(item_url, headers=accounts["seller"]["headers"], json=ship)
    ).status_code == 409
    await client.post(f"/api/v1/orders/{order['id']}/payments/local", headers=headers)
    assert (
        await client.post(
            item_url, headers=accounts["seller"]["headers"], json={**ship, "status": "delivered"}
        )
    ).status_code == 409
    for _ in range(2):
        assert (
            await client.post(item_url, headers=accounts["seller"]["headers"], json=ship)
        ).status_code == 200
    assert (
        await client.post(
            item_url,
            headers=accounts["seller"]["headers"],
            json={"status": "delivered", "tracking_number": "CHANGED"},
        )
    ).status_code == 409
    assert (
        await client.delete(
            "/api/v1/addresses/" + body["address_id"], headers=accounts["buyer2"]["headers"]
        )
    ).status_code == 404
    assert (
        await client.delete("/api/v1/addresses/" + body["address_id"], headers=headers)
    ).status_code == 204
    snapshot = (await client.get(f"/api/v1/orders/{order['id']}", headers=headers)).json()
    assert snapshot["shipping_address"]["line1"] == ADDRESS["line1"]
