from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class DocumentType(str, Enum):
    resume = "resume"
    cover_letter = "cover_letter"


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    type: DocumentType
    content: str = ""


class DocumentCreate(SQLModel):
    job_id: int
    type: DocumentType
    content: str = ""


class DocumentRead(SQLModel):
    id: int
    job_id: int
    type: DocumentType
    content: str
