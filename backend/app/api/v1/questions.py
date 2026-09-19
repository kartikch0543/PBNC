import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.models.document import Document
from app.models.question import Question, QuestionStatus, QuestionType
from app.models.user import User
from app.schemas.question import QuestionListResponse, QuestionResponse

router = APIRouter(tags=["Questions"])


@router.get(
    "/documents/{document_id}/questions",
    response_model=QuestionListResponse,
    summary="Retrieve all extracted questions for a document",
)
async def get_document_questions(
    document_id: uuid.UUID,
    status: Optional[QuestionStatus] = Query(None, description="Filter by question status"),
    question_type: Optional[QuestionType] = Query(None, description="Filter by question type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionListResponse:
    """
    Retrieves extracted structured questions for a document with status counters.
    Ensures that only the document owner can access the data.
    """
    # Verify document ownership
    doc_query = select(Document).where(Document.id == document_id)
    doc = (await db.execute(doc_query)).scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundError("Document", document_id)
    if doc.user_id != current_user.id:
        raise PermissionDeniedError("You do not have permission to view questions for this document")

    # Base query
    query = select(Question).where(Question.document_id == document_id)
    if status:
        query = query.where(Question.status == status)
    if question_type:
        query = query.where(Question.question_type == question_type)
    query = query.order_by(Question.created_at.asc())

    questions = list((await db.execute(query)).scalars().all())

    # Calculate status counts across all questions for this document
    all_q_query = select(Question.status, func.count(Question.id)).where(
        Question.document_id == document_id
    ).group_by(Question.status)
    status_counts = dict((await db.execute(all_q_query)).all())

    return QuestionListResponse(
        total_count=len(questions),
        extracted_count=status_counts.get(QuestionStatus.EXTRACTED, 0),
        partial_count=status_counts.get(QuestionStatus.PARTIAL, 0),
        review_required_count=status_counts.get(QuestionStatus.REVIEW_REQUIRED, 0),
        questions=[QuestionResponse.model_validate(q) for q in questions],
    )


@router.get(
    "/questions/{question_id}",
    response_model=QuestionResponse,
    summary="Retrieve individual question details by ID",
)
async def get_question_detail(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionResponse:
    """Retrieves full details of an individual question."""
    query = select(Question).where(Question.id == question_id)
    question = (await db.execute(query)).scalar_one_or_none()
    if not question:
        raise ResourceNotFoundError("Question", question_id)

    # Check ownership via parent document
    doc = (await db.execute(select(Document).where(Document.id == question.document_id))).scalar_one_or_none()
    if not doc or doc.user_id != current_user.id:
        raise PermissionDeniedError("You do not have access to this question")

    return QuestionResponse.model_validate(question)


@router.get(
    "/documents/{document_id}/answers",
    summary="Retrieve extracted answer keys and matched answers for a document",
)
async def get_document_answers(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns a consolidated summary of questions with their detected answers."""
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundError("Document", document_id)
    if doc.user_id != current_user.id:
        raise PermissionDeniedError("You do not have access to this document")

    query = select(Question).where(Question.document_id == document_id).order_by(Question.created_at.asc())
    questions = list((await db.execute(query)).scalars().all())

    answers = [
        {
            "question_id": q.id,
            "question_number": q.question_number,
            "detected_answer": q.detected_answer,
            "answer_source": q.answer_source,
            "confidence_score": q.confidence_score,
            "status": q.status,
            "source_pages": q.source_pages,
        }
        for q in questions
    ]
    return {
        "document_id": document_id,
        "total_questions": len(questions),
        "answered_questions": sum(1 for q in questions if q.detected_answer is not None),
        "answers": answers,
    }
