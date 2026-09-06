import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(20), nullable=False)
    publisher_id = Column(UUID(as_uuid=True), ForeignKey("publishers.id"))
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"))
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id"))
    subject = Column(Text, nullable=False)
    class_ = Column("class", Integer, nullable=False)
    board = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)
    marks = Column(Integer, nullable=False)
    difficulty = Column(String(10), nullable=False)
    cognitive_level = Column(String(20))
    language = Column(String(5), default="en")
    question_text = Column(Text, nullable=False)
    options = Column(JSONB)
    answer = Column(Text, nullable=False)
    solution = Column(Text)
    has_media = Column(Boolean, default=False)
    media = Column(JSONB, default=list)
    concept_tags = Column(ARRAY(Text), default=list)
    usage_count = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    chapter = relationship("Chapter", back_populates="questions")
    usage_records = relationship("QuestionUsage", back_populates="question")


class QuestionUsage(Base):
    __tablename__ = "question_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"))
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id"), nullable=False)
    batch_id = Column(Text)
    asked_on = Column(DateTime(timezone=True), default=datetime.utcnow)

    question = relationship("Question", back_populates="usage_records")
