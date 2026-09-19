import datetime
import logging
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ProcessingStatus
from app.models.job import JobStatus, ProcessingJob
from app.models.question import AnswerSource, Question, QuestionStatus, QuestionType
from app.models.warning import ExtractionWarning, WarningCode
from app.services.answer_key import answer_key_service
from app.services.confidence import confidence_calculator
from app.services.extractor import question_extractor
from app.services.ocr_engine import PageContent, ocr_engine
from app.services.vision_ai import vision_ai_service

logger = logging.getLogger(__name__)


async def run_pipeline(db: AsyncSession, document: Document, job: ProcessingJob) -> None:
    """
    Executes the complete document intelligence workflow:
    1. Preprocessing & OCR text extraction
    2. Optional Vision AI fallback for scans
    3. Question & Option boundary segmentation
    4. Answer-key detection & association
    5. Explainable confidence calculation & warning collection
    6. Database persistence
    """
    logger.info(f"Starting pipeline execution for document {document.id} ({document.original_filename})")

    # Step 1: Preprocessing & Text Extraction
    job.progress_pct = 25
    job.current_step = "Extracting document pages and text streams"
    await db.commit()

    pages: List[PageContent] = ocr_engine.process_file(document.file_path, document.mime_type)
    document.page_count = len(pages)
    await db.commit()

    # Step 2: Vision AI on scans if available and document has scanned pages
    ai_questions = []
    ai_answer_key = {}
    any_scanned = any(p.is_scanned for p in pages)

    if any_scanned and vision_ai_service.is_available():
        job.progress_pct = 40
        job.current_step = "Executing Vision AI multimodal analysis for scanned pages"
        await db.commit()

        for p in pages:
            if p.image_bytes:
                ai_result = await vision_ai_service.extract_from_image(p.image_bytes)
                if ai_result:
                    if "questions" in ai_result:
                        ai_questions.extend(ai_result["questions"])
                    if "answer_key" in ai_result:
                        ai_answer_key.update(ai_result["answer_key"])

    # Step 3: Question Boundary Segmentation
    job.progress_pct = 60
    job.current_step = "Segmenting questions, options, and page continuity"
    await db.commit()

    pages_data = [(p.page_number, p.text) for p in pages]
    raw_questions, extracted_answer_key = question_extractor.extract_from_pages(pages_data)

    # Merge any answer key from Vision AI
    extracted_answer_key.update(ai_answer_key)

    # Convert raw questions into Question database model entities
    db_questions: List[Question] = []
    for raw in raw_questions:
        q = Question(
            document_id=document.id,
            question_number=raw.question_number,
            question_text=raw.question_text,
            question_type=raw.question_type,
            options=raw.options,
            detected_answer=raw.detected_answer,
            answer_source=AnswerSource.INLINE if raw.detected_answer else AnswerSource.UNMATCHED,
            source_pages=raw.source_pages,
            has_diagram=raw.has_diagram,
        )
        db_questions.append(q)

    # If rule-based extractor found nothing on scanned doc but Vision AI did, map Vision AI
    if not db_questions and ai_questions:
        for item in ai_questions:
            q_type_str = item.get("question_type", "MULTIPLE_CHOICE")
            try:
                q_type = QuestionType(q_type_str)
            except ValueError:
                q_type = QuestionType.UNKNOWN

            db_questions.append(
                Question(
                    document_id=document.id,
                    question_number=item.get("question_number"),
                    question_text=item.get("question_text", ""),
                    question_type=q_type,
                    options=item.get("options", []),
                    detected_answer=item.get("detected_answer"),
                    answer_source=AnswerSource.INLINE if item.get("detected_answer") else AnswerSource.UNMATCHED,
                    source_pages=[1],
                    has_diagram=item.get("has_diagram", False),
                )
            )

    # Step 4: Answer-Key Detection & Association
    job.progress_pct = 75
    job.current_step = "Detecting and associating answer keys"
    await db.commit()

    matched_pairs = answer_key_service.match_answers(db_questions, extracted_answer_key)

    # Step 5: Confidence Calculation & Warning Logging
    job.progress_pct = 85
    job.current_step = "Calculating confidence metrics and generating review flags"
    await db.commit()

    all_warnings: List[ExtractionWarning] = []

    for q, match_warning in matched_pairs:
        if match_warning:
            all_warnings.append(match_warning)

        # Calculate explainable confidence score
        score, status, conf_warnings = confidence_calculator.evaluate(
            q=q,
            is_scanned_page=any_scanned,
        )
        q.confidence_score = score
        q.status = status
        all_warnings.extend(conf_warnings)

    # Step 6: Atomic Database Persistence
    job.progress_pct = 95
    job.current_step = "Saving structured questions and audit warnings"
    await db.commit()

    # Add questions and warnings to session
    for q in db_questions:
        db.add(q)
    await db.flush()

    for w in all_warnings:
        # Ensure question_id is set if warning matches question
        db.add(w)

    # Finalize Job & Document Status
    job.progress_pct = 100
    job.status = JobStatus.COMPLETED
    job.current_step = f"Extracted {len(db_questions)} questions ({len(all_warnings)} review items)"
    job.completed_at = datetime.datetime.now(datetime.timezone.utc)

    if all_warnings:
        document.processing_status = ProcessingStatus.COMPLETED_WITH_WARNINGS
    else:
        document.processing_status = ProcessingStatus.COMPLETED

    await db.commit()
    logger.info(f"Successfully finished pipeline for document {document.id}")
