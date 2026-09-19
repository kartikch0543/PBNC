"""Initial schema setup

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-19 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. Documents table
    document_type_enum = postgresql.ENUM("QUESTION_PAPER", "ANSWER_KEY", "UNSPECIFIED", name="document_type_enum")
    document_type_enum.create(op.get_bind(), checkfirst=True)

    processing_status_enum = postgresql.ENUM("PENDING", "PROCESSING", "COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED", name="processing_status_enum")
    processing_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False, unique=True),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("document_type", sa.Enum("QUESTION_PAPER", "ANSWER_KEY", "UNSPECIFIED", name="document_type_enum"), nullable=False, server_default="UNSPECIFIED"),
        sa.Column("processing_status", sa.Enum("PENDING", "PROCESSING", "COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED", name="processing_status_enum"), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_documents_user_id"), "documents", ["user_id"], unique=False)
    op.create_index(op.f("ix_documents_file_hash"), "documents", ["file_hash"], unique=False)
    op.create_index(op.f("ix_documents_processing_status"), "documents", ["processing_status"], unique=False)

    # 3. Document Relationships table
    relationship_type_enum = postgresql.ENUM("ANSWER_KEY_FOR", "SUPPLEMENT_TO", name="relationship_type_enum")
    relationship_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "document_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.Enum("ANSWER_KEY_FOR", "SUPPLEMENT_TO", name="relationship_type_enum"), nullable=False, server_default="ANSWER_KEY_FOR"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_document_id", "target_document_id", name="uq_document_pair"),
    )
    op.create_index(op.f("ix_document_relationships_source_document_id"), "document_relationships", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_document_relationships_target_document_id"), "document_relationships", ["target_document_id"], unique=False)

    # 4. Processing Jobs table
    job_status_enum = postgresql.ENUM("QUEUED", "PROCESSING", "COMPLETED", "FAILED", name="job_status_enum")
    job_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("QUEUED", "PROCESSING", "COMPLETED", "FAILED", name="job_status_enum"), nullable=False, server_default="QUEUED"),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_step", sa.String(length=255), nullable=False, server_default="Job queued for processing"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_processing_jobs_document_id"), "processing_jobs", ["document_id"], unique=False)
    op.create_index(op.f("ix_processing_jobs_status"), "processing_jobs", ["status"], unique=False)

    # 5. Questions table
    question_type_enum = postgresql.ENUM("MULTIPLE_CHOICE", "MULTI_SELECT", "TRUE_FALSE", "SHORT_ANSWER", "ESSAY", "UNKNOWN", name="question_type_enum")
    question_type_enum.create(op.get_bind(), checkfirst=True)

    answer_source_enum = postgresql.ENUM("INLINE", "DOCUMENT_END", "RELATED_DOCUMENT", "UNMATCHED", name="answer_source_enum")
    answer_source_enum.create(op.get_bind(), checkfirst=True)

    question_status_enum = postgresql.ENUM("EXTRACTED", "PARTIAL", "REVIEW_REQUIRED", "FAILED", name="question_status_enum")
    question_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_number", sa.String(length=50), nullable=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.Enum("MULTIPLE_CHOICE", "MULTI_SELECT", "TRUE_FALSE", "SHORT_ANSWER", "ESSAY", "UNKNOWN", name="question_type_enum"), nullable=False, server_default="UNKNOWN"),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("detected_answer", sa.String(length=255), nullable=True),
        sa.Column("answer_source", sa.Enum("INLINE", "DOCUMENT_END", "RELATED_DOCUMENT", "UNMATCHED", name="answer_source_enum"), nullable=False, server_default="UNMATCHED"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("status", sa.Enum("EXTRACTED", "PARTIAL", "REVIEW_REQUIRED", "FAILED", name="question_status_enum"), nullable=False, server_default="EXTRACTED"),
        sa.Column("source_pages", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("has_diagram", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_questions_document_id"), "questions", ["document_id"], unique=False)
    op.create_index(op.f("ix_questions_question_number"), "questions", ["question_number"], unique=False)
    op.create_index(op.f("ix_questions_status"), "questions", ["status"], unique=False)

    # 6. Extraction Warnings table
    warning_code_enum = postgresql.ENUM(
        "MISSING_QUESTION_NUMBER",
        "AMBIGUOUS_OPTIONS",
        "SPLIT_PAGE_CONTINUATION",
        "LOW_OCR_CONFIDENCE",
        "UNMATCHED_ANSWER_KEY",
        "UNEXPECTED_LAYOUT",
        "POSSIBLE_TRUNCATION",
        name="warning_code_enum"
    )
    warning_code_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "extraction_warnings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("warning_code", sa.Enum("MISSING_QUESTION_NUMBER", "AMBIGUOUS_OPTIONS", "SPLIT_PAGE_CONTINUATION", "LOW_OCR_CONFIDENCE", "UNMATCHED_ANSWER_KEY", "UNEXPECTED_LAYOUT", "POSSIBLE_TRUNCATION", name="warning_code_enum"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_extraction_warnings_document_id"), "extraction_warnings", ["document_id"], unique=False)
    op.create_index(op.f("ix_extraction_warnings_question_id"), "extraction_warnings", ["question_id"], unique=False)
    op.create_index(op.f("ix_extraction_warnings_warning_code"), "extraction_warnings", ["warning_code"], unique=False)


def downgrade() -> None:
    op.drop_table("extraction_warnings")
    op.execute("DROP TYPE IF EXISTS warning_code_enum")

    op.drop_table("questions")
    op.execute("DROP TYPE IF EXISTS question_status_enum")
    op.execute("DROP TYPE IF EXISTS answer_source_enum")
    op.execute("DROP TYPE IF EXISTS question_type_enum")

    op.drop_table("processing_jobs")
    op.execute("DROP TYPE IF EXISTS job_status_enum")

    op.drop_table("document_relationships")
    op.execute("DROP TYPE IF EXISTS relationship_type_enum")

    op.drop_table("documents")
    op.execute("DROP TYPE IF EXISTS processing_status_enum")
    op.execute("DROP TYPE IF EXISTS document_type_enum")

    op.drop_table("users")
