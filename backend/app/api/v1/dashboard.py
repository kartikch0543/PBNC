import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.document import Document, ProcessingStatus
from app.models.question import Question, QuestionStatus
from app.models.warning import ExtractionWarning
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    summary="Retrieve aggregated dashboard metrics and recent processing jobs",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returns aggregate KPI metrics and recent processing jobs for the authenticated user:
    - total documents
    - total questions
    - questions requiring review
    - failed jobs count
    - recent processing jobs list with question counts and warnings
    """
    # 1. Total documents for current user
    doc_count_q = select(func.count(Document.id)).where(Document.user_id == current_user.id)
    total_documents = (await db.execute(doc_count_q)).scalar() or 0

    # 2. Total questions and review required questions
    q_stats_q = (
        select(
            func.count(Question.id),
            func.sum(
                case(
                    (Question.status == QuestionStatus.REVIEW_REQUIRED, 1),
                    (Question.confidence_score < 0.80, 1),
                    else_=0,
                )
            ),
        )
        .select_from(Question)
        .join(Document, Question.document_id == Document.id)
        .where(Document.user_id == current_user.id)
    )
    q_stats_res = (await db.execute(q_stats_q)).one_or_none()
    total_questions = q_stats_res[0] if q_stats_res and q_stats_res[0] else 0
    review_required_count = q_stats_res[1] if q_stats_res and q_stats_res[1] else 0

    # 3. Failed jobs count
    failed_q = (
        select(func.count(Document.id))
        .where(Document.user_id == current_user.id)
        .where(Document.processing_status == ProcessingStatus.FAILED)
    )
    failed_jobs_count = (await db.execute(failed_q)).scalar() or 0

    # 4. Recent processing jobs (latest 10)
    recent_docs_q = (
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .limit(10)
    )
    recent_docs = list((await db.execute(recent_docs_q)).scalars().all())

    recent_jobs = []
    for d in recent_docs:
        # Question count
        q_count = (
            await db.execute(
                select(func.count(Question.id)).where(Question.document_id == d.id)
            )
        ).scalar() or 0

        # Warning count
        warn_count = (
            await db.execute(
                select(func.count(ExtractionWarning.id)).where(ExtractionWarning.document_id == d.id)
            )
        ).scalar() or 0

        recent_jobs.append(
            {
                "id": str(d.id),
                "original_filename": d.original_filename,
                "document_type": d.document_type.value,
                "processing_status": d.processing_status.value,
                "file_size_bytes": d.file_size_bytes,
                "page_count": d.page_count,
                "question_count": q_count,
                "warning_count": warn_count,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
        )

    return {
        "total_documents": total_documents,
        "total_questions": total_questions,
        "review_required_count": review_required_count,
        "failed_jobs_count": failed_jobs_count,
        "recent_jobs": recent_jobs,
    }
