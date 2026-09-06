import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class Publisher(Base):
    __tablename__ = "publishers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True)
    logo_url = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    books = relationship("Book", back_populates="publisher")


class Book(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publisher_id = Column(UUID(as_uuid=True), ForeignKey("publishers.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    class_ = Column("class", Integer, nullable=False)
    board = Column(Text, nullable=False)
    edition = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    publisher = relationship("Publisher", back_populates="books")
    chapters = relationship("Chapter", back_populates="book")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    chapter_name = Column(Text, nullable=False)
    content_text = Column(Text)
    subtopics = Column(JSONB, default=list)
    processing_status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    book = relationship("Book", back_populates="chapters")
    chunks = relationship("ChapterChunk", back_populates="chapter")
    questions = relationship("Question", back_populates="chapter")

    __table_args__ = (UniqueConstraint("book_id", "chapter_number"),)


class ChapterChunk(Base):
    __tablename__ = "chapter_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    chapter = relationship("Chapter", back_populates="chunks")

    __table_args__ = (UniqueConstraint("chapter_id", "chunk_index"),)
