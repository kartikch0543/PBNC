import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.question import Question


class WarningCode(str, enum.Enum):
    MISSING_QUESTION_NUMBER = "MISSING_QUESTION_NUMBER"
    AMBIGUOUS_OPTIONS = "AMBIGUOUS_OPTIONS"
    SPLIT_PAGE_CONTINUATION = "SPLIT_PAGE_CONTINUATION"
    LOW_OCR_CONFIDENCE = "LOW_OCR_CONFIDENCE"
    UNMATCHED_ANSWER_KEY = "UNMATCHED_ANSWER_KEY"
    UNEXPECTED_LAYOUT = "UNEXPECTED_LAYOUT"
    POSSIBLE_TRUNCATION = "POSSIBLE_TRUNCATION"


class ExtractionWarning(Base):
    """Traceable review item associated with a document and optionally a specific question."""
    __tablename__ = "extraction_warnings"

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
    question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    warning_code: Mapped[WarningCode] = mapped_column(
        Enum(WarningCode, name="warning_code_enum"),
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_page: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="warnings")
    question: Mapped[Optional["Question"]] = relationship("Question", back_populates="warnings")

    def __repr__(self) -> str:
        return f"<ExtractionWarning id={self.id} code={self.warning_code} page={self.source_page}>"
