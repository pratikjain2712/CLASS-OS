"""
Platform admin + institute admin endpoints.
Covers: institute CRUD, branch CRUD, user creation, publisher/book/chapter management,
bulk question import from Excel.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import openpyxl
import io

from app.database import get_db
from app.middleware.auth import get_current_user, hash_password, require_roles
from app.models.institute import Institute, Branch, User, InstituteSubscription
from app.models.content import Publisher, Book, Chapter
from app.models.questions import Question
from app.schemas.institute import (
    InstituteCreate, InstituteOut, BranchCreate, BranchOut, UserCreate, UserOut
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ─── Institutes ───────────────────────────────────────────────────────────────

@router.get("/institutes", response_model=list[InstituteOut])
async def list_institutes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("platform_admin")),
):
    result = await db.execute(select(Institute).order_by(Institute.name))
    return result.scalars().all()


@router.post("/institutes", response_model=InstituteOut, status_code=201)
async def create_institute(
    payload: InstituteCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("platform_admin")),
):
    inst = Institute(**payload.model_dump())
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return inst


# ─── Branches ─────────────────────────────────────────────────────────────────

@router.get("/institutes/{institute_id}/branches", response_model=list[BranchOut])
async def list_branches(
    institute_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("platform_admin", "institute_admin") and current_user.institute_id != institute_id:
        raise HTTPException(403, "Access denied")
    result = await db.execute(
        select(Branch).where(Branch.institute_id == institute_id).order_by(Branch.name)
    )
    return result.scalars().all()


@router.post("/institutes/{institute_id}/branches", response_model=BranchOut, status_code=201)
async def create_branch(
    institute_id: UUID,
    payload: BranchCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("platform_admin", "institute_admin")),
):
    branch = Branch(institute_id=institute_id, **payload.model_dump())
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch


# ─── Users ────────────────────────────────────────────────────────────────────

@router.post("/institutes/{institute_id}/users", response_model=UserOut, status_code=201)
async def create_user(
    institute_id: UUID,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("platform_admin", "institute_admin", "branch_admin"):
        raise HTTPException(403, "Insufficient permissions")

    user = User(
        institute_id=institute_id,
        branch_id=payload.branch_id,
        role=payload.role,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ─── Publishers / Books / Chapters ────────────────────────────────────────────

@router.post("/publishers", status_code=201)
async def create_publisher(
    name: str,
    logo_url: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("platform_admin")),
):
    pub = Publisher(name=name, logo_url=logo_url)
    db.add(pub)
    await db.commit()
    await db.refresh(pub)
    return {"id": str(pub.id), "name": pub.name}


@router.post("/books", status_code=201)
async def create_book(
    publisher_id: UUID,
    title: str,
    subject: str,
    class_: int,
    board: str,
    edition: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("platform_admin")),
):
    book = Book(
        publisher_id=publisher_id, title=title, subject=subject,
        class_=class_, board=board, edition=edition
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return {"id": str(book.id), "title": book.title}


@router.post("/books/{book_id}/chapters", status_code=201)
async def create_chapter(
    book_id: UUID,
    chapter_number: int,
    chapter_name: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("platform_admin")),
):
    ch = Chapter(book_id=book_id, chapter_number=chapter_number, chapter_name=chapter_name)
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return {"id": str(ch.id), "chapter_name": ch.chapter_name}


# ─── Bulk Question Import (Excel) ─────────────────────────────────────────────

REQUIRED_COLS = {
    "chapter_id", "question_type", "marks", "difficulty",
    "question_text", "answer", "source_type"
}


@router.post("/questions/bulk-import")
async def bulk_import_questions(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("platform_admin")),
):
    """
    Import questions from Excel.
    Expected columns (row 1 = header):
      chapter_id | question_type | marks | difficulty | question_text |
      options_json | answer | solution | concept_tags | source_type |
      cognitive_level | language
    """
    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active

    headers = [str(cell.value).strip().lower() if cell.value else "" for cell in ws[1]]
    missing = REQUIRED_COLS - set(headers)
    if missing:
        raise HTTPException(400, f"Missing columns: {missing}")

    col_idx = {h: i for i, h in enumerate(headers)}

    def cell(row, col_name):
        idx = col_idx.get(col_name)
        return row[idx].value if idx is not None else None

    chapters_cache: dict[str, Chapter] = {}
    imported = 0
    errors = []

    for row_num, row in enumerate(ws.iter_rows(min_row=2), start=2):
        try:
            chapter_id_str = str(cell(row, "chapter_id") or "").strip()
            if not chapter_id_str:
                continue

            if chapter_id_str not in chapters_cache:
                ch = await db.get(Chapter, UUID(chapter_id_str))
                if not ch:
                    errors.append(f"Row {row_num}: chapter_id {chapter_id_str} not found")
                    continue
                chapters_cache[chapter_id_str] = ch
            ch = chapters_cache[chapter_id_str]

            book = await db.get(Book, ch.book_id)
            if not book:
                errors.append(f"Row {row_num}: book not found for chapter {chapter_id_str}")
                continue

            import json
            options_raw = cell(row, "options_json")
            options = json.loads(options_raw) if options_raw else None

            tags_raw = cell(row, "concept_tags")
            tags = [t.strip() for t in str(tags_raw).split(",")] if tags_raw else []

            q = Question(
                source_type=str(cell(row, "source_type") or "publisher_bank"),
                chapter_id=ch.id,
                book_id=ch.book_id,
                publisher_id=book.publisher_id,
                subject=book.subject,
                class_=book.class_,
                board=book.board,
                question_type=str(cell(row, "question_type") or "").strip(),
                marks=int(cell(row, "marks") or 1),
                difficulty=str(cell(row, "difficulty") or "Medium").strip(),
                question_text=str(cell(row, "question_text") or "").strip(),
                options=options,
                answer=str(cell(row, "answer") or "").strip(),
                solution=str(cell(row, "solution") or "") or None,
                concept_tags=tags,
                cognitive_level=str(cell(row, "cognitive_level") or "") or None,
                language=str(cell(row, "language") or "en"),
                is_approved=True,
            )
            db.add(q)
            imported += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {e}")

    await db.commit()
    return {"imported": imported, "errors": errors}
