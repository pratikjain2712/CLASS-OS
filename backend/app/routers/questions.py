from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.institute import User
from app.models.questions import Question, QuestionUsage
from app.schemas.questions import QuestionOut, QuestionCreate
from app.schemas.content import ChapterQuestionCount

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("", response_model=list[QuestionOut])
async def list_questions(
    chapter_ids: list[UUID] = Query(default=[]),
    difficulty: str | None = None,
    question_type: str | None = None,
    marks: int | None = None,
    batch_id: str | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Question).where(Question.is_approved == True)
    if chapter_ids:
        stmt = stmt.where(Question.chapter_id.in_(chapter_ids))
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if question_type:
        stmt = stmt.where(Question.question_type == question_type)
    if marks:
        stmt = stmt.where(Question.marks == marks)

    stmt = stmt.order_by(Question.usage_count.asc()).limit(limit)
    result = await db.execute(stmt)
    questions = result.scalars().all()

    # Mark already-asked questions
    recently_asked_ids: set[UUID] = set()
    if batch_id and questions:
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        asked_stmt = select(QuestionUsage.question_id).where(
            QuestionUsage.institute_id == current_user.institute_id,
            QuestionUsage.batch_id == batch_id,
            QuestionUsage.asked_on >= six_months_ago,
            QuestionUsage.question_id.in_([q.id for q in questions]),
        )
        asked_result = await db.execute(asked_stmt)
        recently_asked_ids = {r[0] for r in asked_result.all()}

    out = []
    for q in questions:
        qo = QuestionOut.model_validate(q)
        qo.already_asked = q.id in recently_asked_ids
        out.append(qo)
    return out


@router.get("/availability", response_model=list[ChapterQuestionCount])
async def question_availability(
    chapter_ids: list[UUID] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Counts per chapter/difficulty — used in Step 4 UI."""
    from app.models.content import Chapter
    result = await db.execute(
        select(Chapter)
        .where(Chapter.id.in_(chapter_ids))
        .order_by(Chapter.chapter_number)
    )
    chapters = result.scalars().all()

    counts = []
    for ch in chapters:
        for diff in ("Easy", "Medium", "Hard"):
            count_res = await db.execute(
                select(func.count(Question.id)).where(
                    Question.chapter_id == ch.id,
                    Question.difficulty == diff,
                    Question.is_approved == True,
                )
            )
        # total
        total_res = await db.execute(
            select(func.count(Question.id)).where(
                Question.chapter_id == ch.id, Question.is_approved == True
            )
        )
        easy_res = await db.execute(select(func.count(Question.id)).where(Question.chapter_id == ch.id, Question.difficulty == "Easy", Question.is_approved == True))
        med_res = await db.execute(select(func.count(Question.id)).where(Question.chapter_id == ch.id, Question.difficulty == "Medium", Question.is_approved == True))
        hard_res = await db.execute(select(func.count(Question.id)).where(Question.chapter_id == ch.id, Question.difficulty == "Hard", Question.is_approved == True))

        counts.append(ChapterQuestionCount(
            chapter_id=ch.id,
            chapter_name=ch.chapter_name,
            chapter_number=ch.chapter_number,
            total=total_res.scalar() or 0,
            easy=easy_res.scalar() or 0,
            medium=med_res.scalar() or 0,
            hard=hard_res.scalar() or 0,
        ))
    return counts


@router.post("", response_model=QuestionOut, status_code=201)
async def create_question(
    payload: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.content import Chapter, Book
    ch = await db.get(Chapter, payload.chapter_id)
    if not ch:
        raise HTTPException(404, "Chapter not found")
    book = await db.get(Book, ch.book_id)

    q = Question(
        source_type="teacher_created",
        chapter_id=payload.chapter_id,
        book_id=ch.book_id,
        publisher_id=book.publisher_id if book else None,
        subject=book.subject if book else "Unknown",
        class_=book.class_ if book else 0,
        board=book.board if book else "CBSE",
        question_type=payload.question_type,
        marks=payload.marks,
        difficulty=payload.difficulty,
        question_text=payload.question_text,
        options=payload.options,
        answer=payload.answer,
        solution=payload.solution,
        concept_tags=payload.concept_tags,
        language=payload.language,
        cognitive_level=payload.cognitive_level,
        is_approved=True,
    )
    db.add(q)
    await db.commit()
    await db.refresh(q)
    return QuestionOut.model_validate(q)
