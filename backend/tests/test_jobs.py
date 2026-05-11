import pytest
from httpx import AsyncClient

_JOB = {
    "title": "Senior Python Engineer",
    "company": "Acme Corp",
    "location": "Remote",
    "url": "https://example.com/jobs/1",
    "description": "Looking for a senior Python engineer.",
    "source": "indeed",
}


@pytest.mark.asyncio
async def test_jobs_require_auth(client: AsyncClient):
    res = await client.get("/api/v1/jobs/")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_list_jobs_empty(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/jobs/", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_create_job(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/jobs/", json=_JOB, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == _JOB["title"]
    assert data["status"] == "new"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_job(client: AsyncClient, auth_headers: dict):
    job_id = (await client.post("/api/v1/jobs/", json=_JOB, headers=auth_headers)).json()["id"]
    res = await client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_job_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/jobs/999", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_job(client: AsyncClient, auth_headers: dict):
    job_id = (await client.post("/api/v1/jobs/", json=_JOB, headers=auth_headers)).json()["id"]
    res = await client.patch(
        f"/api/v1/jobs/{job_id}",
        json={"status": "applied", "score": 85.0},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "applied"
    assert res.json()["score"] == 85.0


@pytest.mark.asyncio
async def test_delete_job(client: AsyncClient, auth_headers: dict):
    job_id = (await client.post("/api/v1/jobs/", json=_JOB, headers=auth_headers)).json()["id"]
    assert (await client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)).status_code == 204
    assert (await client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_list_jobs_status_filter(client: AsyncClient, auth_headers: dict):
    job1_id = (await client.post("/api/v1/jobs/", json=_JOB, headers=auth_headers)).json()["id"]
    job2 = {**_JOB, "url": "https://example.com/jobs/2"}
    await client.post("/api/v1/jobs/", json=job2, headers=auth_headers)
    await client.patch(f"/api/v1/jobs/{job1_id}", json={"status": "applied"}, headers=auth_headers)

    res = await client.get("/api/v1/jobs/?status=applied", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == job1_id


@pytest.mark.asyncio
async def test_trigger_scrape(client: AsyncClient, auth_headers: dict):
    res = await client.post(
        "/api/v1/jobs/scrape",
        json={"keywords": "python developer", "location": "Remote"},
        headers=auth_headers,
    )
    assert res.status_code == 202
    assert res.json()["message"] == "Scrape queued"
