from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.middleware.auth import get_current_user, require_roles
from app.models.institute import User
from app.models.papers import Paper, PaperTemplate, PaperQuestion
from app.models.questions import Question, QuestionUsage
from app.schemas.papers import (
    PaperGenerateRequest, PaperOut, PaperWithQuestionsOut,
    QuestionSwapRequest, PaperAvailabilityOut
)
from app.services.paper_generator import generate_bank_paper, check_availability

router = APIRouter(prefix="/api/papers", tags=["papers"])


def _batch_id(paper: Paper) -> str:
    section = f" {paper.section}" if paper.section else ""
    return f"Class {paper.class_}{section}"


@router.get("/availability", response_model=PaperAvailabilityOut)
async def check_question_availability(
    template_id: UUID,
    chapter_ids: list[UUID],
    difficulty: str = "Mixed",
    batch_id: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Step 4: show available question counts before generating."""
    sections = await check_availability(
        db=db,
        template_id=template_id,
        chapter_ids=chapter_ids,
        difficulty=difficulty,
        batch_id=batch_id,
        institute_id=current_user.institute_id,
    )
    total = sum(s["available_fresh"] for s in sections)
    any_shortfall = any(s["shortfall"] for s in sections)
    return PaperAvailabilityOut(
        template_id=template_id,
        chapter_ids=chapter_ids,
        difficulty=difficulty,
        sections=sections,
        total_available=total,
        shortfall=any_shortfall,
    )


@router.post("/generate", response_model=PaperWithQuestionsOut, status_code=201)
async def generate_paper(
    payload: PaperGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = await db.execute(
        select(PaperTemplate)
        .options(selectinload(PaperTemplate.sections))
        .where(PaperTemplate.id == payload.template_id)
    )
    template = template.scalar_one_or_none()
    if not template:
        raise HTTPException(404, "Template not found")

    paper = Paper(
        institute_id=current_user.institute_id,
        branch_id=current_user.branch_id,
        created_by=current_user.id,
        title=payload.title,
        class_=payload.class_,
        section=payload.section,
        subject=payload.subject,
        board=payload.board,
        publisher_id=payload.publisher_id,
        template_id=payload.template_id,
        chapter_ids=payload.chapter_ids,
        generation_mode=payload.generation_mode,
        language=payload.language,
        total_marks=template.total_marks,
        status="draft",
    )
    db.add(paper)
    await db.flush()  # get paper.id

    batch_id = _batch_id(paper)

    if payload.generation_mode == "bank":
        pqs, shortfall = await generate_bank_paper(
            db=db,
            paper=paper,
            template=template,
            chapter_ids=payload.chapter_ids,
            difficulty=payload.difficulty,
            batch_id=batch_id,
        )
        for pq in pqs:
            db.add(pq)

        # Record usage
        for pq in pqs:
            db.add(QuestionUsage(
                question_id=pq.question_id,
                paper_id=paper.id,
                institute_id=current_user.institute_id,
                batch_id=batch_id,
            ))
    else:
        raise HTTPException(400, "AI generation not yet implemented — use mode='bank'")

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Paper)
        .options(
            selectinload(Paper.paper_questions).selectinload(PaperQuestion.question)
        )
        .where(Paper.id == paper.id)
    )
    paper = result.scalar_one()

    # Annotate already_asked flag
    recently_asked_pq_ids = await _get_recently_asked(db, paper, batch_id)
    for pq in paper.paper_questions:
        pq.question.already_asked = pq.question_id in recently_asked_pq_ids

    return _build_paper_response(paper, shortfall)


@router.get("/{paper_id}", response_model=PaperWithQuestionsOut)
async def get_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = await _load_paper(db, paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    _check_access(paper, current_user)
    return _build_paper_response(paper, [])


@router.get("", response_model=list[PaperOut])
async def list_papers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Paper)
    if current_user.role == "teacher":
        stmt = stmt.where(Paper.created_by == current_user.id)
    elif current_user.role == "branch_admin":
        stmt = stmt.where(Paper.branch_id == current_user.branch_id)
    else:
        stmt = stmt.where(Paper.institute_id == current_user.institute_id)

    stmt = stmt.order_by(Paper.created_at.desc()).limit(100)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/{paper_id}/questions/{pq_id}/swap", response_model=PaperWithQuestionsOut)
async def swap_question(
    paper_id: UUID,
    pq_id: UUID,
    payload: QuestionSwapRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.paper_generator import swap_question as svc_swap
    from app.models.questions import Question as Q

    paper = await _load_paper(db, paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    _check_access(paper, current_user)

    old_pq = next((pq for pq in paper.paper_questions if pq.id == pq_id), None)
    if not old_pq:
        raise HTTPException(404, "Question slot not found")

    old_question_id = old_pq.question_id
    await svc_swap(db, paper, old_pq, payload.new_question_id)
    await db.commit()

    # Log the swap event
    from app.models.papers import Paper as P
    from sqlalchemy import text
    await db.execute(
        text("""
            INSERT INTO question_events
              (question_id, paper_id, teacher_id, institute_id, branch_id, event_type, swap_reason)
            VALUES (:qid, :pid, :tid, :iid, :bid, 'swapped_out', :reason)
        """),
        {
            "qid": str(old_question_id),
            "pid": str(paper_id),
            "tid": str(current_user.id),
            "iid": str(current_user.institute_id),
            "bid": str(current_user.branch_id) if current_user.branch_id else None,
            "reason": payload.swap_reason,
        }
    )
    await db.commit()

    paper = await _load_paper(db, paper_id)
    return _build_paper_response(paper, [])


@router.post("/{paper_id}/finalize", response_model=PaperOut)
async def finalize_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    _check_access(paper, current_user)
    paper.status = "final"
    paper.updated_at = datetime.utcnow()
    await db.commit()
    return paper


# ─── helpers ──────────────────────────────────────────────────────────────────

async def _load_paper(db: AsyncSession, paper_id: UUID) -> Paper | None:
    result = await db.execute(
        select(Paper)
        .options(selectinload(Paper.paper_questions).selectinload(PaperQuestion.question))
        .where(Paper.id == paper_id)
    )
    return result.scalar_one_or_none()


def _check_access(paper: Paper, user: User):
    if user.role == "teacher" and paper.created_by != user.id:
        raise HTTPException(403, "Access denied")
    if user.role == "branch_admin" and paper.branch_id != user.branch_id:
        raise HTTPException(403, "Access denied")
    if paper.institute_id != user.institute_id:
        raise HTTPException(403, "Access denied")


async def _get_recently_asked(db: AsyncSession, paper: Paper, batch_id: str) -> set[UUID]:
    from datetime import timedelta
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    question_ids = [pq.question_id for pq in paper.paper_questions]
    result = await db.execute(
        select(QuestionUsage.question_id).where(
            QuestionUsage.institute_id == paper.institute_id,
            QuestionUsage.batch_id == batch_id,
            QuestionUsage.asked_on >= six_months_ago,
            QuestionUsage.question_id.in_(question_ids),
        )
    )
    return {r[0] for r in result.all()}


def _build_paper_response(paper: Paper, shortfall: list[dict]) -> PaperWithQuestionsOut:
    from app.schemas.papers import PaperWithQuestionsOut, PaperQuestionOut
    from app.schemas.questions import QuestionOut

    pqs_out = []
    for pq in paper.paper_questions:
        q = pq.question
        qo = QuestionOut.model_validate(q)
        qo.already_asked = getattr(q, "already_asked", False)
        pqs_out.append(PaperQuestionOut(
            id=pq.id,
            section_label=pq.section_label,
            question_order=pq.question_order,
            marks=pq.marks,
            set_variant=pq.set_variant,
            question=qo,
        ))

    return PaperWithQuestionsOut(
        id=paper.id,
        institute_id=paper.institute_id,
        branch_id=paper.branch_id,
        created_by=paper.created_by,
        title=paper.title,
        class_=paper.class_,
        section=paper.section,
        subject=paper.subject,
        board=paper.board,
        publisher_id=paper.publisher_id,
        template_id=paper.template_id,
        chapter_ids=paper.chapter_ids or [],
        generation_mode=paper.generation_mode,
        language=paper.language,
        total_marks=paper.total_marks,
        status=paper.status,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
        paper_questions=pqs_out,
        shortfall=shortfall,
    )
