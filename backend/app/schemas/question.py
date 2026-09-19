import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.question import AnswerSource, QuestionStatus, QuestionType


class OptionItem(BaseModel):
    """Structured question option."""
    key: str = Field(description="Option key, e.g. A, B, (a), 1")
    text: str = Field(description="Option text content")
    is_correct: Optional[bool] = Field(default=None, description="True if marked as correct answer")


class QuestionResponse(BaseModel):
    """Structured output schema for an extracted question."""
    id: uuid.UUID
    document_id: uuid.UUID
    question_number: Optional[str] = Field(
        default=None, description="Original question number from document, or null if unnumbered"
    )
    question_text: str = Field(description="Full question stem")
    question_type: QuestionType
    options: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    detected_answer: Optional[str] = Field(
        default=None, description="Associated answer identifier or answer text"
    )
    answer_source: AnswerSource
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Composite explainable confidence metric"
    )
    status: QuestionStatus
    source_pages: List[int] = Field(
        description="1-indexed source pages from which question was extracted"
    )
    has_diagram: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    """Paginated list of questions with summary metrics."""
    total_count: int
    extracted_count: int
    partial_count: int
    review_required_count: int
    questions: List[QuestionResponse]
