from typing import Any, Dict, List, Optional, Tuple
from app.models.question import AnswerSource, Question, QuestionStatus, QuestionType
from app.models.warning import ExtractionWarning, WarningCode


class ConfidenceCalculator:
    """
    Computes an explainable, deterministic confidence score (0.0 - 1.0)
    based on objective extraction signals and generates actionable review warnings.
    """

    @classmethod
    def evaluate(
        cls,
        q: Question,
        is_scanned_page: bool = False,
    ) -> Tuple[float, QuestionStatus, List[ExtractionWarning]]:
        score = 1.0
        warnings: List[ExtractionWarning] = []

        # 1. Question Numbering Signal
        if not q.question_number:
            score -= 0.25
            warnings.append(
                ExtractionWarning(
                    document_id=q.document_id,
                    question_id=q.id,
                    warning_code=WarningCode.MISSING_QUESTION_NUMBER,
                    message="Question has no detected question number in the source text",
                    source_page=q.source_pages[0] if q.source_pages else None,
                )
            )

        # 2. Text Content & Truncation Signal
        if len(q.question_text.strip()) < 15:
            score -= 0.30
            warnings.append(
                ExtractionWarning(
                    document_id=q.document_id,
                    question_id=q.id,
                    warning_code=WarningCode.POSSIBLE_TRUNCATION,
                    message="Question stem is unusually short (< 15 characters); possible truncation",
                    source_page=q.source_pages[0] if q.source_pages else None,
                )
            )

        # 3. Option Completeness Signal
        if q.question_type == QuestionType.MULTIPLE_CHOICE:
            opt_count = len(q.options) if q.options else 0
            if opt_count < 2:
                score -= 0.35
                warnings.append(
                    ExtractionWarning(
                        document_id=q.document_id,
                        question_id=q.id,
                        warning_code=WarningCode.AMBIGUOUS_OPTIONS,
                        message=f"Multiple choice question has only {opt_count} extracted options (expected at least 2)",
                        source_page=q.source_pages[0] if q.source_pages else None,
                    )
                )
            elif opt_count == 2:
                # Often standard for True/False or boolean, slight warning if marked MCQ
                score -= 0.05

        # 4. Multi-Page Continuation Signal
        if len(q.source_pages) > 1:
            score -= 0.05
            warnings.append(
                ExtractionWarning(
                    document_id=q.document_id,
                    question_id=q.id,
                    warning_code=WarningCode.SPLIT_PAGE_CONTINUATION,
                    message=f"Question spans across multiple pages: {q.source_pages}",
                    source_page=q.source_pages[0] if q.source_pages else None,
                )
            )

        # 5. Answer Match Status Signal
        if q.answer_source == AnswerSource.UNMATCHED or not q.detected_answer:
            score -= 0.10

        # 6. OCR / Scanned Quality Signal
        if is_scanned_page:
            score -= 0.10

        # Bound score between 0.0 and 1.0
        final_score = max(0.0, min(1.0, round(score, 2)))

        # Derive QuestionStatus
        if final_score >= 0.80:
            status = QuestionStatus.EXTRACTED
        elif final_score >= 0.50:
            status = QuestionStatus.REVIEW_REQUIRED
        else:
            status = QuestionStatus.PARTIAL

        return final_score, status, warnings


confidence_calculator = ConfidenceCalculator()
