import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from app.database import Base


class PdfIngestionJob(Base):
    __tablename__ = "pdf_ingestion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False)
    file_url = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    pages_processed = Column(Integer, default=0)
    total_pages = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AiGenerationJob(Base):
    __tablename__ = "ai_generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id"), nullable=False)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"))
    chapter_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    requirements = Column(JSONB)
    status = Column(String(20), default="pending")
    credits_reserved = Column(Integer, default=0)
    credits_consumed = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
