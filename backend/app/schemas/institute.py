from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class InstituteCreate(BaseModel):
    name: str
    logo_url: str | None = None
    subscription_plan: str = "trial"


class InstituteOut(BaseModel):
    id: UUID
    name: str
    logo_url: str | None
    subscription_plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BranchCreate(BaseModel):
    name: str
    city: str | None = None
    address: str | None = None


class BranchOut(BaseModel):
    id: UUID
    institute_id: UUID
    name: str
    city: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    branch_id: UUID | None = None


class UserOut(BaseModel):
    id: UUID
    institute_id: UUID
    branch_id: UUID | None
    role: str
    name: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
