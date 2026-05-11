from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    resume_text: str = ""
    notification_email: str = ""
    skills: list[str] = Field(default=[], sa_column=Column(JSON))
    scoring_criteria: dict[str, Any] = Field(default={}, sa_column=Column(JSON))


class UserProfileCreate(SQLModel):
    resume_text: str = ""
    notification_email: str = ""
    skills: list[str] = []
    scoring_criteria: dict[str, Any] = {}


class UserProfileUpdate(SQLModel):
    resume_text: Optional[str] = None
    notification_email: Optional[str] = None
    skills: Optional[list[str]] = None
    scoring_criteria: Optional[dict[str, Any]] = None


class UserProfileRead(SQLModel):
    id: int
    resume_text: str
    notification_email: str
    skills: list[str]
    scoring_criteria: dict[str, Any]


class ParsedResumeResponse(SQLModel):
    resume_text: str
    skills: list[str]
    keywords: list[str]
