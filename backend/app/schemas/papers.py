from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from .questions import QuestionOut


class PaperGenerateRequest(BaseModel):
    title: str
    class_: int
    section: str | None = None
    subject: str
    board: str
    publisher_id: UUID
    template_id: UUID
    chapter_ids: list[UUID]
    difficulty: str = "Mixed"  # Easy | Medium | Hard | Mixed
    generation_mode: str = "bank"  # bank | ai
    language: str = "en"


class PaperQuestionOut(BaseModel):
    id: UUID
    section_label: str
    question_order: int
    marks: int
    set_variant: str
    question: QuestionOut

    model_config = {"from_attributes": True}


class PaperOut(BaseModel):
    id: UUID
    institute_id: UUID
    branch_id: UUID | None
    created_by: UUID
    title: str
    class_: int
    section: str | None
    subject: str
    board: str
    publisher_id: UUID | None
    template_id: UUID | None
    chapter_ids: list[UUID]
    generation_mode: str
    language: str
    total_marks: int | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class PaperWithQuestionsOut(PaperOut):
    paper_questions: list[PaperQuestionOut]
    shortfall: list[dict] = []  # sections that couldn't be fully filled


class QuestionSwapRequest(BaseModel):
    new_question_id: UUID
    swap_reason: str | None = None


class PaperAvailabilityOut(BaseModel):
    """Question count by section before generation — shown in Step 4."""
    template_id: UUID
    chapter_ids: list[UUID]
    difficulty: str
    sections: list[dict]  # [{section_label, question_type, marks, requested, available}]
    total_available: int
    shortfall: bool
