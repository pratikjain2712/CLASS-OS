from uuid import UUID
from pydantic import BaseModel


class TemplateSectionOut(BaseModel):
    id: UUID
    section_label: str
    question_type: str
    marks_per_question: int
    question_count: int
    difficulty_mix: dict
    sort_order: int

    model_config = {"from_attributes": True}


class TemplateOut(BaseModel):
    id: UUID
    name: str
    total_marks: int
    is_system_default: bool
    sections: list[TemplateSectionOut]

    model_config = {"from_attributes": True}
