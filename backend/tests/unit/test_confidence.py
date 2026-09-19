import uuid
from app.models.question import AnswerSource, Question, QuestionStatus, QuestionType
from app.models.warning import WarningCode
from app.services.confidence import ConfidenceCalculator


def test_high_confidence_clean_question():
    doc_id = uuid.uuid4()
    q = Question(
        document_id=doc_id,
        question_number="1",
        question_text="What is the capital of France?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[
            {"key": "A", "text": "Berlin"},
            {"key": "B", "text": "Paris"},
            {"key": "C", "text": "Rome"},
            {"key": "D", "text": "Madrid"},
        ],
        detected_answer="B",
        answer_source=AnswerSource.DOCUMENT_END,
        source_pages=[1],
    )

    score, status, warnings = ConfidenceCalculator.evaluate(q, is_scanned_page=False)
    assert score == 1.0
    assert status == QuestionStatus.EXTRACTED
    assert len(warnings) == 0


def test_degraded_confidence_on_missing_number():
    doc_id = uuid.uuid4()
    q = Question(
        document_id=doc_id,
        question_number=None,  # Missing question number
        question_text="Explain the principles of thermodynamics in detail.",
        question_type=QuestionType.ESSAY,
        options=[],
        detected_answer=None,
        answer_source=AnswerSource.UNMATCHED,
        source_pages=[1],
    )

    score, status, warnings = ConfidenceCalculator.evaluate(q, is_scanned_page=False)
    # Penalized for missing number (-0.25) and unmatched answer (-0.10)
    assert score <= 0.65
    assert status == QuestionStatus.REVIEW_REQUIRED
    warning_codes = [w.warning_code for w in warnings]
    assert WarningCode.MISSING_QUESTION_NUMBER in warning_codes


def test_low_confidence_on_ambiguous_options():
    doc_id = uuid.uuid4()
    q = Question(
        document_id=doc_id,
        question_number="3",
        question_text="Which of the following is correct?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[{"key": "A", "text": "Only one option extracted"}],  # Incomplete options
        detected_answer=None,
        answer_source=AnswerSource.UNMATCHED,
        source_pages=[1],
    )

    score, status, warnings = ConfidenceCalculator.evaluate(q, is_scanned_page=False)
    assert score < 0.60
    warning_codes = [w.warning_code for w in warnings]
    assert WarningCode.AMBIGUOUS_OPTIONS in warning_codes
