import pytest
from httpx import AsyncClient

_JOB = {
    "title": "Python Developer",
    "company": "TechCorp",
    "location": "Remote",
    "url": "https://example.com/jobs/doc-test",
    "source": "indeed",
}


async def _create_job(client: AsyncClient, auth_headers: dict) -> int:
    res = await client.post("/api/v1/jobs/", json=_JOB, headers=auth_headers)
    assert res.status_code == 201
    return res.json()["id"]


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/documents/", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_create_document(client: AsyncClient, auth_headers: dict):
    job_id = await _create_job(client, auth_headers)
    res = await client.post(
        "/api/v1/documents/",
        json={"job_id": job_id, "type": "resume", "content": "# Resume\n\nMy tailored resume."},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["type"] == "resume"
    assert data["job_id"] == job_id


@pytest.mark.asyncio
async def test_get_document(client: AsyncClient, auth_headers: dict):
    job_id = await _create_job(client, auth_headers)
    doc_id = (
        await client.post(
            "/api/v1/documents/",
            json={"job_id": job_id, "type": "cover_letter", "content": "Dear Hiring Manager..."},
            headers=auth_headers,
        )
    ).json()["id"]
    res = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/documents/999", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient, auth_headers: dict):
    job_id = await _create_job(client, auth_headers)
    doc_id = (
        await client.post(
            "/api/v1/documents/",
            json={"job_id": job_id, "type": "resume", "content": "Resume content"},
            headers=auth_headers,
        )
    ).json()["id"]
    assert (
        await client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    ).status_code == 204
    assert (
        await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    ).status_code == 404


@pytest.mark.asyncio
async def test_list_documents_by_job_id(client: AsyncClient, auth_headers: dict):
    job1_id = await _create_job(client, auth_headers)
    job2_id = (
        await client.post(
            "/api/v1/jobs/",
            json={**_JOB, "url": "https://example.com/jobs/doc-test-2"},
            headers=auth_headers,
        )
    ).json()["id"]

    for job_id in (job1_id, job2_id):
        await client.post(
            "/api/v1/documents/",
            json={"job_id": job_id, "type": "resume", "content": f"Resume for job {job_id}"},
            headers=auth_headers,
        )

    res = await client.get(f"/api/v1/documents/?job_id={job1_id}", headers=auth_headers)
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) == 1
    assert docs[0]["job_id"] == job1_id


@pytest.mark.asyncio
async def test_documents_require_auth(client: AsyncClient):
    res = await client.get("/api/v1/documents/")
    assert res.status_code == 401
