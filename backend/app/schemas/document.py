import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.document import DocumentType, ProcessingStatus, RelationshipType
from app.models.job import JobStatus


class DocumentUploadResponse(BaseModel):
    """Immediate response after file validation and upload acceptance."""
    document_id: uuid.UUID
    job_id: uuid.UUID
    original_filename: str
    file_size_bytes: int
    mime_type: str
    document_type: DocumentType
    processing_status: ProcessingStatus
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Full document detail schema."""
    id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    file_size_bytes: int
    mime_type: str
    page_count: int
    document_type: DocumentType
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcessingJobResponse(BaseModel):
    """Detailed asynchronous job execution progress."""
    job_id: uuid.UUID
    document_id: uuid.UUID
    status: JobStatus
    progress_pct: int
    current_step: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentRelationshipCreate(BaseModel):
    """Request payload for linking two documents (e.g. Question Paper and Answer Key)."""
    target_document_id: uuid.UUID = Field(
        description="UUID of the related document (e.g. the Answer Key PDF)"
    )
    relationship_type: RelationshipType = Field(
        default=RelationshipType.ANSWER_KEY_FOR,
        description="Relationship type between source and target documents",
    )


class DocumentRelationshipResponse(BaseModel):
    """Response payload for document relationships."""
    id: uuid.UUID
    source_document_id: uuid.UUID
    target_document_id: uuid.UUID
    relationship_type: RelationshipType
    created_at: datetime

    class Config:
        from_attributes = True
