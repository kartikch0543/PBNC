import enum
import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.job import ProcessingJob
    from app.models.question import Question
    from app.models.warning import ExtractionWarning


class DocumentType(str, enum.Enum):
    QUESTION_PAPER = "QUESTION_PAPER"
    ANSWER_KEY = "ANSWER_KEY"
    UNSPECIFIED = "UNSPECIFIED"


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"


class RelationshipType(str, enum.Enum):
    ANSWER_KEY_FOR = "ANSWER_KEY_FOR"
    SUPPLEMENT_TO = "SUPPLEMENT_TO"


class Document(Base, TimestampMixin):
    """Stores uploaded document metadata, processing status, and security hashes."""
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type_enum"),
        default=DocumentType.UNSPECIFIED,
        nullable=False,
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status_enum"),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="documents")
    jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(ProcessingJob.created_at)",
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Question.created_at",
    )
    warnings: Mapped[List["ExtractionWarning"]] = relationship(
        "ExtractionWarning",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    # Relationships to other documents (e.g. Answer Key for Question Paper)
    outgoing_relationships: Mapped[List["DocumentRelationship"]] = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.source_document_id",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    incoming_relationships: Mapped[List["DocumentRelationship"]] = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.target_document_id",
        back_populates="target_document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.original_filename} status={self.processing_status}>"


class DocumentRelationship(Base, TimestampMixin):
    """Explicitly links related documents (e.g. QuestionPaper.pdf <-> AnswerKey.pdf)."""
    __tablename__ = "document_relationships"
    __table_args__ = (
        UniqueConstraint("source_document_id", "target_document_id", name="uq_document_pair"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type_enum"),
        default=RelationshipType.ANSWER_KEY_FOR,
        nullable=False,
    )

    source_document: Mapped["Document"] = relationship(
        "Document",
        foreign_keys=[source_document_id],
        back_populates="outgoing_relationships",
    )
    target_document: Mapped["Document"] = relationship(
        "Document",
        foreign_keys=[target_document_id],
        back_populates="incoming_relationships",
    )
