import pytest
from httpx import AsyncClient

_PROFILE = {
    "resume_text": "Experienced software engineer with 5+ years of Python experience.",
    "notification_email": "test@example.com",
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "scoring_criteria": {
        "keywords": ["python", "fastapi"],
        "exclude": ["php"],
        "remote": True,
    },
}


@pytest.mark.asyncio
async def test_get_profile_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/profile/", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_profile(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/profile/", json=_PROFILE, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["notification_email"] == _PROFILE["notification_email"]
    assert data["skills"] == _PROFILE["skills"]
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/profile/", json=_PROFILE, headers=auth_headers)
    res = await client.get("/api/v1/profile/", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["notification_email"] == _PROFILE["notification_email"]


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/profile/", json=_PROFILE, headers=auth_headers)
    res = await client.patch(
        "/api/v1/profile/",
        json={"notification_email": "new@example.com"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["notification_email"] == "new@example.com"
    assert res.json()["skills"] == _PROFILE["skills"]


@pytest.mark.asyncio
async def test_create_profile_conflict(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/profile/", json=_PROFILE, headers=auth_headers)
    res = await client.post("/api/v1/profile/", json=_PROFILE, headers=auth_headers)
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_profile_requires_auth(client: AsyncClient):
    res = await client.get("/api/v1/profile/")
    assert res.status_code == 401
