import logging
import uuid
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.question import AnswerSource, Question
from app.models.warning import ExtractionWarning, WarningCode

logger = logging.getLogger(__name__)


class AnswerKeyService:
    """
    Manages detection, matching, and cross-document reconciliation of answer keys.
    Distinguishes:
    - CONFIDENT_MATCH
    - POSSIBLE_MATCH
    - UNMATCHED (explicitly preserved as None, raising a warning)
    """

    @classmethod
    def match_answers(
        cls,
        questions: List[Question],
        answer_key: Dict[str, str],
        source: AnswerSource = AnswerSource.DOCUMENT_END,
    ) -> List[Tuple[Question, Optional[ExtractionWarning]]]:
        """
        Associates answers with questions based on exact or normalized question numbering.
        Validates candidate answer against extracted question options so that ambiguous or
        unreliable answers are flagged rather than silently assigned.
        """
        results: List[Tuple[Question, Optional[ExtractionWarning]]] = []
        num_to_letter = {"1": "A", "2": "B", "3": "C", "4": "D"}

        for q in questions:
            warning: Optional[ExtractionWarning] = None

            # Skip if already has an inline detected answer
            if q.detected_answer and q.answer_source == AnswerSource.INLINE:
                results.append((q, None))
                continue

            if not q.question_number:
                # Unnumbered questions cannot be reliably mapped to an answer key
                q.detected_answer = None
                q.answer_source = AnswerSource.UNMATCHED
                warning = ExtractionWarning(
                    document_id=q.document_id,
                    question_id=q.id,
                    warning_code=WarningCode.UNMATCHED_ANSWER_KEY,
                    message="Question has no question number; unable to match against answer key",
                    source_page=q.source_pages[0] if q.source_pages else None,
                )
                results.append((q, warning))
                continue

            # Attempt exact or normalized lookup
            normalized_num = q.question_number.strip().lstrip("Q").lstrip(".").strip()
            raw_answer_val = answer_key.get(normalized_num) or answer_key.get(q.question_number)

            if not raw_answer_val:
                # No answer found in answer key
                q.detected_answer = None
                q.answer_source = AnswerSource.UNMATCHED
                warning = ExtractionWarning(
                    document_id=q.document_id,
                    question_id=q.id,
                    warning_code=WarningCode.UNMATCHED_ANSWER_KEY,
                    message=f"No answer key entry found for Question {q.question_number}",
                    source_page=q.source_pages[0] if q.source_pages else None,
                )
                results.append((q, warning))
                continue

            # Check reliability against question options if available
            answer_val = raw_answer_val.strip().upper()
            valid_opt_keys = {
                opt.get("key", "").upper()
                for opt in (q.options or [])
                if isinstance(opt, dict) and opt.get("key")
            }

            if valid_opt_keys:
                if answer_val in valid_opt_keys:
                    q.detected_answer = answer_val
                    q.answer_source = source
                    results.append((q, None))
                elif answer_val in num_to_letter and num_to_letter[answer_val] in valid_opt_keys:
                    # Mapped numeric key style (e.g. 1 -> A)
                    q.detected_answer = num_to_letter[answer_val]
                    q.answer_source = source
                    results.append((q, None))
                else:
                    # Reliability check failed: answer key entry does not match available options.
                    # Flag with warning rather than silently assigning an invalid answer.
                    q.detected_answer = None
                    q.answer_source = AnswerSource.UNMATCHED
                    warning = ExtractionWarning(
                        document_id=q.document_id,
                        question_id=q.id,
                        warning_code=WarningCode.UNMATCHED_ANSWER_KEY,
                        message=(
                            f"Answer key entry '{raw_answer_val}' cannot be reliably assigned: "
                            f"does not match any available option {sorted(list(valid_opt_keys))} for Question {q.question_number}"
                        ),
                        source_page=q.source_pages[0] if q.source_pages else None,
                    )
                    results.append((q, warning))
            else:
                # Question has no options (e.g. short answer / subjective)
                q.detected_answer = answer_val
                q.answer_source = source
                results.append((q, None))

        return results


async def reconcile_related_documents(
    db: AsyncSession, source_doc_id: uuid.UUID, answer_key_doc_id: uuid.UUID
) -> int:
    """
    Called when a user establishes a document relationship between a Question Paper
    and a separate Answer Key document. Parses the answer key document and reconciles
    answers for all questions in the question paper with option-validation safeguards.
    """
    from app.services.ocr_engine import ocr_engine
    from app.services.extractor import question_extractor

    # 1. Load answer key document
    ans_doc = (await db.execute(select(Document).where(Document.id == answer_key_doc_id))).scalar_one_or_none()
    if not ans_doc:
        return 0

    pages = ocr_engine.process_file(ans_doc.file_path, ans_doc.mime_type)
    pages_data = [(p.page_number, p.text) for p in pages]
    _, answer_key_dict = question_extractor.extract_from_pages(pages_data)

    if not answer_key_dict:
        logger.info(f"No answer key pairs detected in related document {answer_key_doc_id}")
        return 0

    # 2. Load questions from source question paper
    q_query = select(Question).where(Question.document_id == source_doc_id)
    questions = list((await db.execute(q_query)).scalars().all())

    num_to_letter = {"1": "A", "2": "B", "3": "C", "4": "D"}
    matched_count = 0

    for q in questions:
        if not q.question_number:
            continue
        norm_num = q.question_number.strip().lstrip("Q").lstrip(".").strip()
        raw_ans = answer_key_dict.get(norm_num) or answer_key_dict.get(q.question_number)
        if raw_ans:
            ans = raw_ans.strip().upper()
            valid_opt_keys = {
                opt.get("key", "").upper()
                for opt in (q.options or [])
                if isinstance(opt, dict) and opt.get("key")
            }
            if valid_opt_keys:
                if ans in valid_opt_keys:
                    q.detected_answer = ans
                    q.answer_source = AnswerSource.RELATED_DOCUMENT
                    matched_count += 1
                elif ans in num_to_letter and num_to_letter[ans] in valid_opt_keys:
                    q.detected_answer = num_to_letter[ans]
                    q.answer_source = AnswerSource.RELATED_DOCUMENT
                    matched_count += 1
            else:
                q.detected_answer = ans
                q.answer_source = AnswerSource.RELATED_DOCUMENT
                matched_count += 1

    await db.commit()
    logger.info(f"Reconciled {matched_count} questions from related answer key document")
    return matched_count


answer_key_service = AnswerKeyService()
