import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class InstituteCredits(Base):
    __tablename__ = "institute_credits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_balance = Column(Integer, default=0)
    total_purchased = Column(Integer, default=0)
    total_used = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id"), nullable=False)
    type = Column(String(10), nullable=False)
    amount = Column(Integer, nullable=False)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
