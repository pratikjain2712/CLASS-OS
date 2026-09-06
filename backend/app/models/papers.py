import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class PaperTemplate(Base):
    __tablename__ = "paper_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False)
    total_marks = Column(Integer, nullable=False)
    is_system_default = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    sections = relationship("PaperTemplateSection", back_populates="template", order_by="PaperTemplateSection.sort_order")
    papers = relationship("Paper", back_populates="template")


class PaperTemplateSection(Base):
    __tablename__ = "paper_template_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("paper_templates.id", ondelete="CASCADE"), nullable=False)
    section_label = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)
    marks_per_question = Column(Integer, nullable=False)
    question_count = Column(Integer, nullable=False)
    difficulty_mix = Column(JSONB, default=lambda: {"Easy": 30, "Medium": 50, "Hard": 20})
    sort_order = Column(Integer, default=0)

    template = relationship("PaperTemplate", back_populates="sections")


class Paper(Base):
    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(Text, nullable=False)
    class_ = Column("class", Integer, nullable=False)
    section = Column(Text)
    subject = Column(Text, nullable=False)
    board = Column(Text, nullable=False)
    publisher_id = Column(UUID(as_uuid=True), ForeignKey("publishers.id"))
    template_id = Column(UUID(as_uuid=True), ForeignKey("paper_templates.id"))
    chapter_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    generation_mode = Column(String(10), default="bank")
    language = Column(String(5), default="en")
    bilingual = Column(Boolean, default=False)
    total_marks = Column(Integer)
    status = Column(String(10), default="draft")
    pdf_url = Column(Text)
    answer_key_pdf_url = Column(Text)
    qr_payload = Column(JSONB)
    print_settings = Column(JSONB, default=lambda: {
        "font_size": 12, "answer_space": 3,
        "margins": "normal", "numbering": "sequential", "sets": 1
    })
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    template = relationship("PaperTemplate", back_populates="papers")
    paper_questions = relationship("PaperQuestion", back_populates="paper", order_by="PaperQuestion.question_order")
    generation_sources = relationship("PaperGenerationSource", back_populates="paper")


class PaperQuestion(Base):
    __tablename__ = "paper_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    section_label = Column(Text, nullable=False)
    question_order = Column(Integer, nullable=False)
    marks = Column(Integer, nullable=False)
    set_variant = Column(String(1), default="A")

    paper = relationship("Paper", back_populates="paper_questions")
    question = relationship("Question")


class PaperGenerationSource(Base):
    __tablename__ = "paper_generation_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(20), nullable=False)
    chapter_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    subtopic_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    page_ranges = Column(JSONB, default=list)
    uploaded_file_url = Column(Text)
    custom_text = Column(Text)
    extracted_content = Column(Text)

    paper = relationship("Paper", back_populates="generation_sources")
