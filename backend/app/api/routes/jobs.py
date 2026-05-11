from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_session
from app.models.job import Job, JobCreate, JobRead, JobStatus, JobUpdate, ScrapeRequest
from app.models.profile import UserProfile
from app.services.scorer import score_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=list[JobRead])
async def list_jobs(
    status: Optional[JobStatus] = None,
    session: AsyncSession = Depends(get_session),
) -> list[Job]:
    query = select(Job)
    if status:
        query = query.where(Job.status == status)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/score-all")
async def score_all_jobs(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    """Score every job with status 'new' against the stored profile criteria."""
    profile_result = await session.execute(select(UserProfile))
    profile = profile_result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not configured — cannot score jobs")

    jobs_result = await session.execute(select(Job).where(Job.status == JobStatus.new))
    jobs = list(jobs_result.scalars().all())

    for job in jobs:
        job.score = score_job(
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            criteria=profile.scoring_criteria,
        )
        job.status = JobStatus.scored
        session.add(job)

    await session.commit()
    return {"scored": len(jobs)}


@router.post("/scrape", status_code=202)
async def trigger_scrape(scrape_in: ScrapeRequest) -> dict:
    # Stub — scraping implementation in Phase 2
    return {
        "message": "Scrape queued",
        "keywords": scrape_in.keywords,
        "location": scrape_in.location,
        "sources": scrape_in.sources,
    }


@router.post("/", response_model=JobRead, status_code=201)
async def create_job(job_in: JobCreate, session: AsyncSession = Depends(get_session)) -> Job:
    job = Job.model_validate(job_in)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: int, session: AsyncSession = Depends(get_session)) -> Job:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: int,
    job_in: JobUpdate,
    session: AsyncSession = Depends(get_session),
) -> Job:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, value in job_in.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


@router.post("/{job_id}/score", response_model=JobRead)
async def score_single_job(
    job_id: int,
    session: AsyncSession = Depends(get_session),
) -> Job:
    """Score one job against the stored profile criteria and mark it as 'scored'."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile_result = await session.execute(select(UserProfile))
    profile = profile_result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not configured — cannot score jobs")

    job.score = score_job(
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        criteria=profile.scoring_criteria,
    )
    job.status = JobStatus.scored
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: int, session: AsyncSession = Depends(get_session)) -> None:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await session.delete(job)
    await session.commit()
