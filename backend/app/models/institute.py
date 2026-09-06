import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Institute(Base):
    __tablename__ = "institutes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    logo_url = Column(Text)
    subscription_plan = Column(String(20), default="trial")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    branches = relationship("Branch", back_populates="institute")
    users = relationship("User", back_populates="institute")
    subscriptions = relationship("InstituteSubscription", back_populates="institute")


class Branch(Base):
    __tablename__ = "branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    city = Column(Text)
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    institute = relationship("Institute", back_populates="branches")
    users = relationship("User", back_populates="branch")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"))
    role = Column(String(20), nullable=False)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    institute = relationship("Institute", back_populates="users")
    branch = relationship("Branch", back_populates="users")
    assignments = relationship("TeacherAssignment", back_populates="teacher")


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    class_ = Column("class", Integer, nullable=False)
    section = Column(String(10))
    subject = Column(Text, nullable=False)

    teacher = relationship("User", back_populates="assignments")


class InstituteSubscription(Base):
    __tablename__ = "institute_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institute_id = Column(UUID(as_uuid=True), ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False)
    board = Column(Text, nullable=False)
    class_ = Column("class", Integer, nullable=False)
    status = Column(String(20), default="trial")
    starts_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))

    institute = relationship("Institute", back_populates="subscriptions")
