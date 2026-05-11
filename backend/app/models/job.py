from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    new = "new"
    scored = "scored"
    applied = "applied"
    rejected = "rejected"


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    company: str
    location: str
    url: str = Field(unique=True)
    description: str = ""
    score: Optional[float] = None
    source: str
    status: JobStatus = JobStatus.new


class JobCreate(SQLModel):
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    source: str
    status: JobStatus = JobStatus.new


class JobUpdate(SQLModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    score: Optional[float] = None
    status: Optional[JobStatus] = None


class JobRead(SQLModel):
    id: int
    title: str
    company: str
    location: str
    url: str
    description: str
    score: Optional[float]
    source: str
    status: JobStatus


class ScrapeRequest(SQLModel):
    keywords: str
    location: str = ""
    sources: list[str] = ["indeed", "linkedin"]
