import pytest
from httpx import AsyncClient

from tests.conftest import TEST_PASSWORD, TEST_USERNAME


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USERNAME, "password": "wrongpassword"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_username(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody", "password": TEST_PASSWORD},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["username"] == TEST_USERNAME


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Logged out"


@pytest.mark.asyncio
async def test_invalid_token_rejected(client: AsyncClient):
    res = await client.get(
        "/api/v1/jobs/",
        headers={"Authorization": "Bearer totally.invalid.token"},
    )
    assert res.status_code == 401
