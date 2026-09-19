import enum
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.warning import ExtractionWarning


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    MULTI_SELECT = "MULTI_SELECT"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"
    UNKNOWN = "UNKNOWN"


class AnswerSource(str, enum.Enum):
    INLINE = "INLINE"
    DOCUMENT_END = "DOCUMENT_END"
    RELATED_DOCUMENT = "RELATED_DOCUMENT"
    UNMATCHED = "UNMATCHED"


class QuestionStatus(str, enum.Enum):
    EXTRACTED = "EXTRACTED"
    PARTIAL = "PARTIAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAILED = "FAILED"


class Question(Base, TimestampMixin):
    """Stores extracted structured question data, options, detected answers, and confidence."""
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable because we never invent question numbers if missing in source!
    question_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type_enum"),
        default=QuestionType.UNKNOWN,
        nullable=False,
    )
    # Structured options: [{"key": "A", "text": "Option A text"}]
    options: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )
    detected_answer: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    answer_source: Mapped[AnswerSource] = mapped_column(
        Enum(AnswerSource, name="answer_source_enum"),
        default=AnswerSource.UNMATCHED,
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    status: Mapped[QuestionStatus] = mapped_column(
        Enum(QuestionStatus, name="question_status_enum"),
        default=QuestionStatus.EXTRACTED,
        nullable=False,
        index=True,
    )
    # 1-indexed pages from which this question was extracted, e.g. [1, 2] for multi-page questions
    source_pages: Mapped[List[int]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    has_diagram: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="questions")
    warnings: Mapped[List["ExtractionWarning"]] = relationship(
        "ExtractionWarning",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id} num={self.question_number} status={self.status} conf={self.confidence_score}>"
