import pytest
from httpx import AsyncClient

from app.services.scorer import score_job

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_CRITERIA = {
    "keywords": ["python", "fastapi", "react"],
    "exclude_keywords": ["php", "unpaid"],
    "location": "San Francisco",
    "remote_preference": False,
    "score_threshold": 70,
}

_PROFILE_DATA = {
    "resume_text": "Software engineer with Python and FastAPI experience.",
    "notification_email": "test@example.com",
    "skills": ["Python", "FastAPI"],
    "scoring_criteria": _CRITERIA,
}

_JOB_DATA = {
    "title": "Python FastAPI React Engineer",
    "company": "Acme Corp",
    "location": "San Francisco, CA",
    "url": "https://example.com/jobs/scorer-test",
    "description": "Build APIs with Python and FastAPI.",
    "source": "indeed",
}

# ---------------------------------------------------------------------------
# Unit tests — score_job() directly, no DB required
# ---------------------------------------------------------------------------


def test_exclude_keyword_zeros_score():
    assert score_job("PHP Developer", "Acme", "Remote", "PHP stack.", _CRITERIA) == 0.0


def test_exclude_keyword_in_description():
    desc = "This is an unpaid internship."
    assert score_job("Engineer", "Acme", "San Francisco", desc, _CRITERIA) == 0.0


def test_all_keywords_match():
    desc = "We use Python, FastAPI, and React."
    # 3/3 keywords = 60, SF location = 40 → 100
    assert score_job("Software Engineer", "Acme", "San Francisco", desc, _CRITERIA) == 100.0


def test_partial_keyword_match():
    desc = "We use Python only."
    # 1/3 keywords = 20, SF location = 40 → 60
    assert score_job("Software Engineer", "Acme", "San Francisco", desc, _CRITERIA) == 60.0


def test_no_keywords_match():
    desc = "Build things with Java."
    # 0/3 keywords = 0, SF location = 40 → 40
    assert score_job("Engineer", "Acme", "San Francisco", desc, _CRITERIA) == 40.0


def test_no_keywords_configured():
    criteria = {**_CRITERIA, "keywords": []}
    # neutral keyword score = 30, wrong city + not remote = 0 → 30
    assert score_job("Engineer", "Acme", "New York", "Some job.", criteria) == 30.0


def test_remote_job_with_remote_preference():
    criteria = {**_CRITERIA, "remote_preference": True}
    desc = "Python work."
    # 1/3 = 20, remote + pref = 40 → 60
    assert score_job("Python Engineer", "Acme", "Remote", desc, criteria) == 60.0


def test_remote_job_without_remote_preference():
    desc = "Python FastAPI React stack."
    # 3/3 = 60, remote (not preferred) = 20 → 80
    assert score_job("Engineer", "Acme", "Remote", desc, _CRITERIA) == 80.0


def test_location_exact_match():
    desc = "Python FastAPI React."
    # 3/3 = 60, location match = 40 → 100
    assert score_job("Engineer", "Acme", "San Francisco, CA", desc, _CRITERIA) == 100.0


def test_location_no_match_with_preference():
    desc = "Python FastAPI React."
    # 3/3 = 60, wrong city = 0 → 60
    assert score_job("Engineer", "Acme", "New York", desc, _CRITERIA) == 60.0


def test_no_location_preference_is_neutral():
    criteria = {**_CRITERIA, "location": ""}
    desc = "Python FastAPI React."
    # 3/3 = 60, no preference = 20 → 80
    assert score_job("Engineer", "Acme", "New York", desc, criteria) == 80.0


def test_case_insensitive_keywords():
    desc = "We use PYTHON and FASTAPI."
    # Python + FastAPI in desc, React in title → 3/3 = 60, SF = 40 → 100
    assert score_job("REACT Developer", "Acme", "San Francisco", desc, _CRITERIA) == 100.0


def test_keyword_match_in_company():
    desc = "Build great software."
    # "react" in company name → 1/3 = 20, SF = 40 → 60
    assert score_job("Engineer", "React Studios", "San Francisco", desc, _CRITERIA) == 60.0


def test_remote_in_title_counts():
    desc = "Python FastAPI React."
    criteria = {**_CRITERIA, "remote_preference": True}
    # "Remote" in title → is_remote=True, remote_pref=True → 40 loc
    # 3/3 = 60 → 100
    assert score_job("Remote Python Engineer", "Acme", "Anywhere", desc, criteria) == 100.0


def test_score_bounded_to_100():
    desc = "Python FastAPI React developer."
    criteria = {**_CRITERIA, "remote_preference": True}
    # Full keyword + remote match → should be exactly 100 (not exceed it)
    result = score_job("Remote Engineer", "Acme", "Remote", desc, criteria)
    assert result <= 100.0


# ---------------------------------------------------------------------------
# Integration tests — scoring HTTP endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_score_single_job(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/profile/", json=_PROFILE_DATA, headers=auth_headers)
    job_id = (
        await client.post("/api/v1/jobs/", json=_JOB_DATA, headers=auth_headers)
    ).json()["id"]

    res = await client.post(f"/api/v1/jobs/{job_id}/score", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["score"] is not None
    assert data["score"] == 100.0
    assert data["status"] == "scored"


@pytest.mark.asyncio
async def test_score_single_job_not_found(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/profile/", json=_PROFILE_DATA, headers=auth_headers)
    res = await client.post("/api/v1/jobs/999/score", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_score_single_job_no_profile(client: AsyncClient, auth_headers: dict):
    job_id = (
        await client.post("/api/v1/jobs/", json=_JOB_DATA, headers=auth_headers)
    ).json()["id"]
    res = await client.post(f"/api/v1/jobs/{job_id}/score", headers=auth_headers)
    assert res.status_code == 404
    assert "Profile" in res.json()["detail"]


@pytest.mark.asyncio
async def test_score_all_jobs(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/profile/", json=_PROFILE_DATA, headers=auth_headers)
    job2 = {**_JOB_DATA, "url": "https://example.com/jobs/scorer-test-2"}
    job1_id = (
        await client.post("/api/v1/jobs/", json=_JOB_DATA, headers=auth_headers)
    ).json()["id"]
    await client.post("/api/v1/jobs/", json=job2, headers=auth_headers)

    res = await client.post("/api/v1/jobs/score-all", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["scored"] == 2

    job = (await client.get(f"/api/v1/jobs/{job1_id}", headers=auth_headers)).json()
    assert job["status"] == "scored"
    assert job["score"] == 100.0


@pytest.mark.asyncio
async def test_score_all_skips_non_new_jobs(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/profile/", json=_PROFILE_DATA, headers=auth_headers)
    job_id = (
        await client.post("/api/v1/jobs/", json=_JOB_DATA, headers=auth_headers)
    ).json()["id"]
    await client.patch(
        f"/api/v1/jobs/{job_id}", json={"status": "applied"}, headers=auth_headers
    )

    res = await client.post("/api/v1/jobs/score-all", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["scored"] == 0


@pytest.mark.asyncio
async def test_score_all_no_profile(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/jobs/", json=_JOB_DATA, headers=auth_headers)
    res = await client.post("/api/v1/jobs/score-all", headers=auth_headers)
    assert res.status_code == 404
