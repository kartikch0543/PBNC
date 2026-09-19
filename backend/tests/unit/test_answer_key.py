import uuid
from app.models.question import AnswerSource, Question, QuestionType
from app.models.warning import WarningCode
from app.services.answer_key import AnswerKeyService


def test_answer_key_matching_exact():
    doc_id = uuid.uuid4()
    q1 = Question(
        document_id=doc_id,
        question_number="1",
        question_text="Question 1 text",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[{"key": "A", "text": "Opt A"}],
        source_pages=[1],
    )
    q2 = Question(
        document_id=doc_id,
        question_number="2",
        question_text="Question 2 text",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[{"key": "B", "text": "Opt B"}],
        source_pages=[1],
    )

    answer_key = {"1": "A", "2": "C"}
    results = AnswerKeyService.match_answers([q1, q2], answer_key)

    assert len(results) == 2
    assert q1.detected_answer == "A"
    assert q1.answer_source == AnswerSource.DOCUMENT_END
    assert q2.detected_answer == "C"
    assert q2.answer_source == AnswerSource.DOCUMENT_END


def test_unmatched_answer_generates_warning():
    doc_id = uuid.uuid4()
    q = Question(
        document_id=doc_id,
        question_number="99",  # Not in answer key
        question_text="Question 99 text",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[],
        source_pages=[1],
    )

    answer_key = {"1": "A"}
    results = AnswerKeyService.match_answers([q], answer_key)

    assert q.detected_answer is None
    assert q.answer_source == AnswerSource.UNMATCHED
    _, warning = results[0]
    assert warning is not None
    assert warning.warning_code == WarningCode.UNMATCHED_ANSWER_KEY
