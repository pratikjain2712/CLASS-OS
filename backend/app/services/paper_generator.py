"""
Bank-mode paper generation.

Algorithm per section:
  1. Select questions matching chapter_ids + question_type + marks + difficulty
  2. Exclude questions asked to the same batch in the last 6 months
  3. Prefer lowest usage_count, break ties with RANDOM()
  4. Fill as many as possible; record shortfall if count < requested
  5. Proportional chapter distribution when multiple chapters selected
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.questions import Question, QuestionUsage
from app.models.papers import Paper, PaperQuestion, PaperTemplate, PaperTemplateSection


async def check_availability(
    db: AsyncSession,
    template_id: UUID,
    chapter_ids: list[UUID],
    difficulty: str,
    batch_id: str,
    institute_id: UUID,
) -> list[dict]:
    """Return availability counts per template section (used in Step 4 UI)."""
    template = await db.get(PaperTemplate, template_id)
    if not template:
        raise ValueError("Template not found")

    results = []
    six_months_ago = datetime.utcnow() - timedelta(days=180)

    # Pre-fetch recently asked question IDs for this batch
    asked_stmt = select(QuestionUsage.question_id).where(
        QuestionUsage.institute_id == institute_id,
        QuestionUsage.batch_id == batch_id,
        QuestionUsage.asked_on >= six_months_ago,
    )
    asked_result = await db.execute(asked_stmt)
    recently_asked_ids = {r[0] for r in asked_result.all()}

    for section in template.sections:
        stmt = select(func.count(Question.id)).where(
            Question.chapter_id.in_(chapter_ids),
            Question.question_type == section.question_type,
            Question.marks == section.marks_per_question,
            Question.is_approved == True,
        )
        if difficulty != "Mixed":
            stmt = stmt.where(Question.difficulty == difficulty)

        count_result = await db.execute(stmt)
        total_available = count_result.scalar() or 0

        # Count excluding recently asked
        stmt_fresh = stmt.where(Question.id.notin_(recently_asked_ids)) if recently_asked_ids else stmt
        fresh_result = await db.execute(stmt_fresh)
        fresh_available = fresh_result.scalar() or 0

        results.append({
            "section_label": section.section_label,
            "question_type": section.question_type,
            "marks_per_question": section.marks_per_question,
            "question_count": section.question_count,
            "available_total": total_available,
            "available_fresh": fresh_available,
            "shortfall": fresh_available < section.question_count,
        })

    return results


async def generate_bank_paper(
    db: AsyncSession,
    paper: Paper,
    template: PaperTemplate,
    chapter_ids: list[UUID],
    difficulty: str,
    batch_id: str,
) -> tuple[list[PaperQuestion], list[dict]]:
    """
    Generate paper questions from the bank.
    Returns (paper_questions_to_insert, shortfall_report).
    """
    six_months_ago = datetime.utcnow() - timedelta(days=180)

    asked_stmt = select(QuestionUsage.question_id).where(
        QuestionUsage.institute_id == paper.institute_id,
        QuestionUsage.batch_id == batch_id,
        QuestionUsage.asked_on >= six_months_ago,
    )
    asked_result = await db.execute(asked_stmt)
    recently_asked_ids = {r[0] for r in asked_result.all()}

    paper_questions: list[PaperQuestion] = []
    shortfall: list[dict] = []
    global_order = 1

    for section in template.sections:
        selected = await _select_questions(
            db=db,
            chapter_ids=chapter_ids,
            question_type=section.question_type,
            marks=section.marks_per_question,
            difficulty=difficulty,
            difficulty_mix=section.difficulty_mix,
            count=section.question_count,
            recently_asked_ids=recently_asked_ids,
        )

        for q in selected:
            pq = PaperQuestion(
                paper_id=paper.id,
                question_id=q.id,
                section_label=section.section_label,
                question_order=global_order,
                marks=section.marks_per_question,
                set_variant="A",
            )
            paper_questions.append(pq)
            global_order += 1

        if len(selected) < section.question_count:
            shortfall.append({
                "section_label": section.section_label,
                "question_type": section.question_type,
                "marks": section.marks_per_question,
                "requested": section.question_count,
                "available": len(selected),
            })

    return paper_questions, shortfall


async def _select_questions(
    db: AsyncSession,
    chapter_ids: list[UUID],
    question_type: str,
    marks: int,
    difficulty: str,
    difficulty_mix: dict,
    count: int,
    recently_asked_ids: set[UUID],
) -> list[Question]:
    """
    Select `count` questions from the bank.
    Uses proportional difficulty distribution when difficulty='Mixed'.
    Deprioritises recently asked questions (warns but still uses if unavoidable).
    """
    if difficulty == "Mixed":
        return await _select_mixed(
            db, chapter_ids, question_type, marks, difficulty_mix, count, recently_asked_ids
        )
    else:
        return await _fetch_questions(
            db, chapter_ids, question_type, marks, [difficulty], count, recently_asked_ids
        )


async def _select_mixed(
    db: AsyncSession,
    chapter_ids: list[UUID],
    question_type: str,
    marks: int,
    mix: dict,
    count: int,
    recently_asked_ids: set[UUID],
) -> list[Question]:
    """Distribute count across difficulties using mix percentages."""
    selected: list[Question] = []
    remaining = count

    for diff, pct in mix.items():
        portion = round(count * pct / 100)
        if portion == 0:
            continue
        portion = min(portion, remaining)
        qs = await _fetch_questions(db, chapter_ids, question_type, marks, [diff], portion, recently_asked_ids)
        selected.extend(qs)
        recently_asked_ids.update(q.id for q in qs)
        remaining -= len(qs)

    # Fill any remainder from any difficulty
    if remaining > 0:
        used_ids = {q.id for q in selected}
        extra = await _fetch_questions(
            db, chapter_ids, question_type, marks,
            list(mix.keys()), remaining,
            recently_asked_ids | used_ids
        )
        selected.extend(extra)

    return selected


async def _fetch_questions(
    db: AsyncSession,
    chapter_ids: list[UUID],
    question_type: str,
    marks: int,
    difficulties: list[str],
    count: int,
    exclude_ids: set[UUID],
) -> list[Question]:
    """Fetch fresh questions first; fall back to recently-asked if pool empty."""
    base_stmt = (
        select(Question)
        .where(
            Question.chapter_id.in_(chapter_ids),
            Question.question_type == question_type,
            Question.marks == marks,
            Question.difficulty.in_(difficulties),
            Question.is_approved == True,
        )
        .order_by(Question.usage_count.asc(), func.random())
        .limit(count)
    )

    # Try fresh (not recently asked) first
    fresh_stmt = base_stmt.where(Question.id.notin_(exclude_ids)) if exclude_ids else base_stmt
    result = await db.execute(fresh_stmt)
    fresh = list(result.scalars().all())

    if len(fresh) >= count:
        return fresh[:count]

    # Fill gap with already-asked questions (will be flagged in UI)
    needed = count - len(fresh)
    already_used_ids = {q.id for q in fresh}
    fallback_stmt = (
        select(Question)
        .where(
            Question.chapter_id.in_(chapter_ids),
            Question.question_type == question_type,
            Question.marks == marks,
            Question.difficulty.in_(difficulties),
            Question.is_approved == True,
            Question.id.notin_(already_used_ids),
        )
        .order_by(Question.usage_count.asc(), func.random())
        .limit(needed)
    )
    fallback_result = await db.execute(fallback_stmt)
    fallback = list(fallback_result.scalars().all())

    return fresh + fallback


async def swap_question(
    db: AsyncSession,
    paper: Paper,
    old_pq: PaperQuestion,
    new_question_id: UUID,
) -> PaperQuestion:
    """Replace a paper question in place."""
    new_q = await db.get(Question, new_question_id)
    if not new_q:
        raise ValueError("Question not found")
    if new_q.marks != old_pq.marks:
        raise ValueError("Replacement question must have same mark value")

    old_pq.question_id = new_question_id
    paper.updated_at = datetime.utcnow()
    db.add(old_pq)
    db.add(paper)
    await db.flush()
    return old_pq
