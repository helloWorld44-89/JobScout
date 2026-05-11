from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_session
from app.models.document import Document, DocumentCreate, DocumentRead

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=list[DocumentRead])
async def list_documents(
    job_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    query = select(Document)
    if job_id is not None:
        query = query.where(Document.job_id == job_id)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/", response_model=DocumentRead, status_code=201)
async def create_document(
    doc_in: DocumentCreate,
    session: AsyncSession = Depends(get_session),
) -> Document:
    doc = Document.model_validate(doc_in)
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


@router.get("/{doc_id}", response_model=DocumentRead)
async def get_document(doc_id: int, session: AsyncSession = Depends(get_session)) -> Document:
    doc = await session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: int, session: AsyncSession = Depends(get_session)) -> None:
    doc = await session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await session.delete(doc)
    await session.commit()
