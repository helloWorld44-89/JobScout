from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_session
from app.models.profile import UserProfile, UserProfileCreate, UserProfileRead, UserProfileUpdate

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
