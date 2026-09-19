import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.models.document import Document
from app.models.user import User
from app.models.warning import ExtractionWarning
from app.schemas.warning import ExtractionWarningResponse

router = APIRouter(tags=["Review & Warnings"])


@router.get(
    "/documents/{document_id}/warnings",
    response_model=List[ExtractionWarningResponse],
    summary="Retrieve all extraction review flags and warnings for a document",
)
async def get_document_warnings(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ExtractionWarning]:
    """
    Returns audit warnings generated during extraction, enabling human QA reviewers
    to inspect anomalies, unnumbered questions, multi-page breaks, and unmatched answers.
    """
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundError("Document", document_id)
    if doc.user_id != current_user.id:
        raise PermissionDeniedError("You do not have access to this document")

    query = (
        select(ExtractionWarning)
        .where(ExtractionWarning.document_id == document_id)
        .order_by(ExtractionWarning.created_at.asc())
    )
    warnings = list((await db.execute(query)).scalars().all())
    return warnings
