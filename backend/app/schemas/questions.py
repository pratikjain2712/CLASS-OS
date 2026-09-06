from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class QuestionCreate(BaseModel):
    chapter_id: UUID
    question_type: str
    marks: int
    difficulty: str
    question_text: str
    options: list[dict] | None = None
    answer: str
    solution: str | None = None
    concept_tags: list[str] = []
    language: str = "en"
    cognitive_level: str | None = None


class QuestionOut(BaseModel):
    id: UUID
    source_type: str
    chapter_id: UUID | None
    publisher_id: UUID | None
    subject: str
    class_: int
    board: str
    question_type: str
    marks: int
    difficulty: str
    cognitive_level: str | None
    language: str
    question_text: str
    options: Any | None
    answer: str
    solution: str | None
    has_media: bool
    media: list
    concept_tags: list[str]
    usage_count: int
    is_approved: bool
    already_asked: bool = False  # populated at query time

    model_config = {"from_attributes": True, "populate_by_name": True}
