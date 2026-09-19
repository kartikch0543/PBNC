import asyncio
import logging
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as db_core
from app.models.document import Document, ProcessingStatus
from app.models.job import JobStatus, ProcessingJob

logger = logging.getLogger(__name__)


async def process_document_pipeline(document_id: str, job_id: str) -> None:
    """
    Main asynchronous pipeline orchestrator for document intelligence:
    1. Update job status to PROCESSING
    2. Digital text extraction (PyMuPDF)
    3. Layout & question boundary segmentation
    4. Option parsing & classification
    5. Answer-key detection & reconciliation
    6. Confidence calculation & warning logging
    7. Update document status to COMPLETED / COMPLETED_WITH_WARNINGS
    """
    doc_uuid = uuid.UUID(document_id)
    job_uuid = uuid.UUID(job_id)

    # Use active session factory from db_core at runtime
    async with db_core.AsyncSessionLocal() as db:
        try:
            # 1. Fetch document and job
            doc_query = select(Document).where(Document.id == doc_uuid)
            document = (await db.execute(doc_query)).scalar_one_or_none()

            job_query = select(ProcessingJob).where(ProcessingJob.id == job_uuid)
            job = (await db.execute(job_query)).scalar_one_or_none()

            if not document or not job:
                logger.error(f"Cannot process: Document {document_id} or Job {job_id} not found")
                return

            # Update job to PROCESSING
            job.status = JobStatus.PROCESSING
            job.progress_pct = 10
            job.current_step = "Inspecting document layout and text streams"
            document.processing_status = ProcessingStatus.PROCESSING
            await db.commit()

            # The actual pipeline execution
            from app.services.pipeline import run_pipeline
            await run_pipeline(db=db, document=document, job=job)

        except Exception as e:
            logger.exception(f"Fatal error processing document {document_id}: {str(e)}")
            try:
                async with db_core.AsyncSessionLocal() as err_db:
                    err_job = (await err_db.execute(select(ProcessingJob).where(ProcessingJob.id == job_uuid))).scalar_one_or_none()
                    err_doc = (await err_db.execute(select(Document).where(Document.id == doc_uuid))).scalar_one_or_none()
                    if err_job:
                        err_job.status = JobStatus.FAILED
                        err_job.error_message = f"Processing failed: {str(e)}"
                    if err_doc:
                        err_doc.processing_status = ProcessingStatus.FAILED
                    await err_db.commit()
            except Exception as inner_ex:
                logger.error(f"Failed to record failure state: {inner_ex}")


async def enqueue_document_job(document_id: uuid.UUID, job_id: uuid.UUID, background_tasks=None) -> None:
    """
    Dispatches document processing job:
    Tries Redis/ARQ first. If Redis is unavailable, immediately runs asynchronously
    in the event loop via asyncio.create_task.
    """
    from app.core.config import settings
    import redis.asyncio as aioredis
    from arq import create_pool
    from arq.connections import RedisSettings

    enqueued = False
    try:
        redis_client = aioredis.from_url(settings.redis_connection_url, socket_connect_timeout=0.5)
        await redis_client.ping()
        await redis_client.aclose()

        # Redis is available, enqueue via ARQ
        redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis_connection_url))
        await redis_pool.enqueue_job("process_document_pipeline", str(document_id), str(job_id))
        await redis_pool.close()
        enqueued = True
        logger.info(f"Enqueued document {document_id} to Redis ARQ queue")
    except Exception:
        # Expected when Redis daemon is not running on host machine
        pass

    if not enqueued:
        logger.info(f"Dispatching document {document_id} via in-process asyncio task")
        asyncio.create_task(process_document_pipeline(str(document_id), str(job_id)))
