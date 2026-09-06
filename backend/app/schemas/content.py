from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class PublisherOut(BaseModel):
    id: UUID
    name: str
    logo_url: str | None

    model_config = {"from_attributes": True}


class BookOut(BaseModel):
    id: UUID
    publisher_id: UUID
    title: str
    subject: str
    class_: int
    board: str
    edition: str | None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ChapterOut(BaseModel):
    id: UUID
    book_id: UUID
    chapter_number: int
    chapter_name: str
    processing_status: str
    subtopics: list

    model_config = {"from_attributes": True}


class ChapterQuestionCount(BaseModel):
    chapter_id: UUID
    chapter_name: str
    chapter_number: int
    total: int
    easy: int
    medium: int
    hard: int
