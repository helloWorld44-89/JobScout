from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_session
from app.models.profile import (
    ParsedResumeResponse,
    UserProfile,
    UserProfileCreate,
    UserProfileRead,
    UserProfileUpdate,
)
from app.services.ai import parse_resume as ai_parse_resume
from app.services.parser import extract_resume_text

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=UserProfileRead)
async def get_profile(session: AsyncSession = Depends(get_session)) -> UserProfile:
    result = await session.execute(select(UserProfile))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not configured")
    return profile


@router.post("/", response_model=UserProfileRead, status_code=201)
async def create_profile(
    profile_in: UserProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> UserProfile:
    result = await session.execute(select(UserProfile))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Profile already exists — use PATCH to update")
    profile = UserProfile.model_validate(profile_in)
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.patch("/", response_model=UserProfileRead)
async def update_profile(
    profile_in: UserProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> UserProfile:
    result = await session.execute(select(UserProfile))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not configured")
    for key, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.post("/parse-resume", response_model=ParsedResumeResponse)
async def parse_resume_endpoint(
    file: UploadFile = File(...),
) -> ParsedResumeResponse:
    content = await file.read()
    text = extract_resume_text(content, file.filename or "upload.txt")
    parsed = await ai_parse_resume(text)
    return ParsedResumeResponse(
        resume_text=text,
        skills=parsed["skills"],
        keywords=parsed["keywords"],
    )
