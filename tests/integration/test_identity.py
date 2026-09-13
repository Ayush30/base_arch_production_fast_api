from uuid import UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.identity.models import User
from tests.conftest import PASSWORD


async def test_registration_verification_and_password_reset(client: AsyncClient) -> None:
    body = {"email": "new@example.com", "password": PASSWORD, "name": "New Buyer"}
    response = await client.post("/api/v1/auth/register", json=body)
    assert response.status_code == 201, response.text
    assert "password_hash" not in response.json()
    assert (await client.post("/api/v1/auth/register", json=body)).status_code == 409
    assert (
        await client.post(
            "/api/v1/auth/register", json={**body, "email": "staff@example.com", "role": "admin"}
        )
    ).status_code == 422
    assert (
        await client.post(
            "/api/v1/auth/login", json={"email": body["email"], "password": "incorrect"}
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login", json={"email": "absent@example.com", "password": PASSWORD}
        )
    ).status_code == 401
    login = (
        await client.post("/api/v1/auth/login", json={"email": body["email"], "password": PASSWORD})
    ).json()
    headers = {"Authorization": "Bearer " + login["access_token"]}
    assert (await client.get("/api/v1/auth/me", headers=headers)).json()["email_verified"] is False
    token = (
        await client.post("/api/v1/auth/verification/request", json={"email": body["email"]})
    ).json()["development_token"]
    assert (
        await client.post("/api/v1/auth/verification/confirm", json={"token": token})
    ).status_code == 204
    assert (
        await client.post("/api/v1/auth/verification/confirm", json={"token": token})
    ).status_code == 400
    assert (await client.get("/api/v1/auth/me", headers=headers)).json()["email_verified"] is True
    reset = (
        await client.post("/api/v1/auth/password/request", json={"email": body["email"]})
    ).json()["development_token"]
    assert (
        await client.post(
            "/api/v1/auth/password/reset", json={"token": reset, "password": "New-password-2026!"}
        )
    ).status_code == 204
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401
    assert (
        await client.post("/api/v1/auth/refresh", json={"token": login["refresh_token"]})
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login", json={"email": body["email"], "password": "New-password-2026!"}
        )
    ).status_code == 200
    assert (
        await client.post("/api/v1/auth/password/request", json={"email": "missing@example.com"})
    ).json()["development_token"] is None


async def test_refresh_rotation_and_logout(client: AsyncClient, accounts: dict) -> None:
    original = accounts["buyer"]
    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"token": original["tokens"]["refresh_token"]}
    )
    assert refreshed.status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/refresh", json={"token": original["tokens"]["refresh_token"]}
        )
    ).status_code == 401
    assert (await client.get("/api/v1/auth/me", headers=original["headers"])).status_code == 401
    headers = {"Authorization": "Bearer " + refreshed.json()["access_token"]}
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 200
    assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 204
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401


async def test_admin_approval_and_immediate_revocation(
    client: AsyncClient, accounts: dict, db_session: AsyncSession
) -> None:
    user = await db_session.get(User, UUID(accounts["seller"]["id"]))
    user.seller_approved = False
    await db_session.commit()
    assert (
        await client.get("/api/v1/seller/products", headers=accounts["seller"]["headers"])
    ).status_code == 403
    url = "/api/v1/admin/users/" + accounts["seller"]["id"]
    assert (
        await client.patch(
            url, headers=accounts["admin"]["headers"], json={"seller_approved": True}
        )
    ).status_code == 200
    assert (
        await client.get("/api/v1/seller/products", headers=accounts["seller"]["headers"])
    ).status_code == 200
    assert (
        await client.patch(url, headers=accounts["admin"]["headers"], json={"is_active": False})
    ).status_code == 200
    assert (
        await client.get("/api/v1/seller/products", headers=accounts["seller"]["headers"])
    ).status_code == 401
    assert (
        await client.patch(
            "/api/v1/admin/users/" + accounts["admin"]["id"],
            headers=accounts["admin"]["headers"],
            json={"is_active": False},
        )
    ).status_code == 400
    assert (
        await client.patch(
            "/api/v1/admin/users/" + accounts["buyer"]["id"],
            headers=accounts["admin"]["headers"],
            json={"seller_approved": True},
        )
    ).status_code == 400
