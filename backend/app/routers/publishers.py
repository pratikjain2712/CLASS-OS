from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.content import Publisher, Book, Chapter
from app.models.institute import User
from app.schemas.content import PublisherOut, BookOut, ChapterOut

router = APIRouter(prefix="/api/publishers", tags=["publishers"])


@router.get("", response_model=list[PublisherOut])
async def list_publishers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Publisher).order_by(Publisher.name))
    return result.scalars().all()


@router.get("/{publisher_id}/books", response_model=list[BookOut])
async def list_books(
    publisher_id: UUID,
    class_: int | None = Query(None, alias="class"),
    subject: str | None = None,
    board: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Book).where(Book.publisher_id == publisher_id)
    if class_:
        stmt = stmt.where(Book.class_ == class_)
    if subject:
        stmt = stmt.where(Book.subject == subject)
    if board:
        stmt = stmt.where(Book.board == board)
    result = await db.execute(stmt.order_by(Book.title))
    return result.scalars().all()


@router.get("/books/{book_id}/chapters", response_model=list[ChapterOut])
async def list_chapters(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chapter)
        .where(Chapter.book_id == book_id)
        .order_by(Chapter.chapter_number)
    )
    return result.scalars().all()
