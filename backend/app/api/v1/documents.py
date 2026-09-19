import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.models.document import Document, DocumentRelationship, DocumentType, ProcessingStatus, RelationshipType
from app.models.job import JobStatus, ProcessingJob
from app.models.user import User
from app.schemas.document import (
    DocumentRelationshipCreate,
    DocumentRelationshipResponse,
    DocumentResponse,
    DocumentUploadResponse,
    ProcessingJobResponse,
)
from app.services.storage import storage_service
from app.workers.tasks import enqueue_document_job

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a PDF or image document for asynchronous intelligence processing",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF, PNG, or JPEG file"),
    document_type: DocumentType = Form(default=DocumentType.UNSPECIFIED),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Validates, streams, and persists an uploaded examination document or answer key.
    Creates a background processing job and immediately returns HTTP 202 Accepted.
    """
    # 1. Save and validate file via storage service
    (
        original_filename,
        stored_filename,
        file_path,
        file_size,
        mime_type,
    ) = await storage_service.save_upload_file(file)

    # Compute SHA-256 for dedup and integrity
    import hashlib
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # 2. Insert Document record
    document = Document(
        user_id=current_user.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_hash=file_hash,
        file_size_bytes=file_size,
        mime_type=mime_type,
        document_type=document_type,
        processing_status=ProcessingStatus.PENDING,
    )
    db.add(document)
    await db.flush()

    # 3. Create ProcessingJob record
    job = ProcessingJob(
        document_id=document.id,
        status=JobStatus.QUEUED,
        progress_pct=0,
        current_step="Document accepted and queued for processing",
    )
    db.add(job)
    await db.commit()
    await db.refresh(document)
    await db.refresh(job)

    # 4. Enqueue asynchronous background job
    await enqueue_document_job(
        document_id=document.id,
        job_id=job.id,
        background_tasks=background_tasks,
    )

    return DocumentUploadResponse(
        document_id=document.id,
        job_id=job.id,
        original_filename=document.original_filename,
        file_size_bytes=document.file_size_bytes,
        mime_type=document.mime_type,
        document_type=document.document_type,
        processing_status=document.processing_status,
        created_at=document.created_at,
    )


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="List all documents owned by the authenticated user",
)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Document]:
    """Retrieves all documents belonging to the authenticated user."""
    query = (
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document metadata by ID",
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """Retrieves metadata of a specific document with authorization verification."""
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise ResourceNotFoundError("Document", document_id)

    if doc.user_id != current_user.id:
        raise PermissionDeniedError("You do not have access to this document")

    return doc


@router.get(
    "/{document_id}/status",
    response_model=ProcessingJobResponse,
    summary="Check current asynchronous processing status and progress",
)
async def get_processing_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessingJobResponse:
    """Retrieves the latest execution job status, current step, and progress percentage."""
    doc_query = select(Document).where(Document.id == document_id)
    doc = (await db.execute(doc_query)).scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundError("Document", document_id)
    if doc.user_id != current_user.id:
        raise PermissionDeniedError("You do not have access to this document")

    job_query = (
        select(ProcessingJob)
        .where(ProcessingJob.document_id == document_id)
        .order_by(ProcessingJob.created_at.desc())
    )
    job = (await db.execute(job_query)).scalars().first()
    if not job:
        raise ResourceNotFoundError("ProcessingJob for Document", document_id)

    return ProcessingJobResponse(
        job_id=job.id,
        document_id=job.document_id,
        status=job.status,
        progress_pct=job.progress_pct,
        current_step=job.current_step,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post(
    "/{document_id}/relationships",
    response_model=DocumentRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Associate two documents (e.g., Question Paper and separate Answer Key)",
)
async def create_document_relationship(
    document_id: uuid.UUID,
    relation_in: DocumentRelationshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRelationship:
    """
    Creates an explicit link between two documents (e.g. QuestionPaper.pdf and AnswerKey.pdf)
    and triggers answer-key reconciliation across documents.
    """
    if document_id == relation_in.target_document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A document cannot be associated with itself",
        )

    # Verify ownership of both documents
    source_doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    target_doc = (await db.execute(select(Document).where(Document.id == relation_in.target_document_id))).scalar_one_or_none()

    if not source_doc:
        raise ResourceNotFoundError("Source Document", document_id)
    if not target_doc:
        raise ResourceNotFoundError("Target Document", relation_in.target_document_id)

    if source_doc.user_id != current_user.id or target_doc.user_id != current_user.id:
        raise PermissionDeniedError("You must own both documents to link them")

    # Check if relationship already exists
    existing = (
        await db.execute(
            select(DocumentRelationship).where(
                DocumentRelationship.source_document_id == document_id,
                DocumentRelationship.target_document_id == relation_in.target_document_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        return existing

    relationship = DocumentRelationship(
        source_document_id=document_id,
        target_document_id=relation_in.target_document_id,
        relationship_type=relation_in.relationship_type,
    )
    db.add(relationship)
    await db.commit()
    await db.refresh(relationship)

    # Trigger answer-key reconciliation
    from app.services.answer_key import reconcile_related_documents
    await reconcile_related_documents(db, document_id, relation_in.target_document_id)

    return relationship


@router.get(
    "/{document_id}/relationships",
    response_model=List[DocumentRelationshipResponse],
    summary="Get all relationships for a document",
)
async def get_document_relationships(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DocumentRelationship]:
    """Retrieves outgoing and incoming relationships for a document."""
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundError("Document", document_id)
    if doc.user_id != current_user.id:
        raise PermissionDeniedError("You do not have access to this document")

    query = select(DocumentRelationship).where(
        (DocumentRelationship.source_document_id == document_id)
        | (DocumentRelationship.target_document_id == document_id)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/samples/{filename}",
    summary="Download pre-generated sample examination file",
)
async def get_sample_document(filename: str):
    """Provides access to curated sample examination documents for 1-click evaluation."""
    import os
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    clean_name = os.path.basename(filename)
    samples_dir = Path(__file__).resolve().parents[3] / "backend" / "samples"
    target_path = samples_dir / clean_name

    if not target_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample file not found")

    mime = "application/pdf" if clean_name.endswith(".pdf") else ("image/png" if clean_name.endswith(".png") else "application/octet-stream")
    return FileResponse(path=str(target_path), filename=clean_name, media_type=mime)
