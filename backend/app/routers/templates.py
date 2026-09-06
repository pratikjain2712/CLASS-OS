from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.institute import User
from app.models.papers import PaperTemplate
from app.schemas.templates import TemplateOut

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    institute_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return system defaults + institute-specific custom templates."""
    stmt = (
        select(PaperTemplate)
        .options(selectinload(PaperTemplate.sections))
        .where(
            or_(
                PaperTemplate.is_system_default == True,
                PaperTemplate.institute_id == (institute_id or current_user.institute_id),
            )
        )
        .order_by(PaperTemplate.total_marks)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
