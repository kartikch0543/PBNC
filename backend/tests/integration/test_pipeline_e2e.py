from pathlib import Path
import pytest
from app.models.question import AnswerSource, Question, QuestionType
from app.services.answer_key import AnswerKeyService
from app.services.confidence import ConfidenceCalculator
from app.services.extractor import QuestionExtractor
from app.services.ocr_engine import OCREngine

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


def test_e2e_clean_digital_pdf():
    pdf_path = SAMPLES_DIR / "sample_01_clean.pdf"
    assert pdf_path.exists()

    pages = OCREngine.process_file(str(pdf_path), "application/pdf")
    assert len(pages) == 1
    assert pages[0].is_scanned is False

    pages_data = [(p.page_number, p.text) for p in pages]
    questions, answer_key = QuestionExtractor.extract_from_pages(pages_data)

    assert len(questions) == 4
    assert questions[0].question_number == "1"
    assert "powerhouse" in questions[0].question_text
    assert len(questions[0].options) == 4

    # Match answers
    db_questions = [
        Question(
            document_id=None,
            question_number=q.question_number,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            source_pages=q.source_pages,
        )
        for q in questions
    ]
    matched = AnswerKeyService.match_answers(db_questions, answer_key)
    assert db_questions[0].detected_answer == "B"
    assert db_questions[1].detected_answer == "C"
    assert db_questions[2].detected_answer == "A"
    assert db_questions[3].detected_answer == "D"


def test_e2e_multi_page_continuation():
    pdf_path = SAMPLES_DIR / "sample_04_multi_page_question.pdf"
    assert pdf_path.exists()

    pages = OCREngine.process_file(str(pdf_path), "application/pdf")
    assert len(pages) == 2

    pages_data = [(p.page_number, p.text) for p in pages]
    questions, answer_key = QuestionExtractor.extract_from_pages(pages_data)

    # Question 2 must span both pages
    q2 = next(q for q in questions if q.question_number == "2")
    assert "accelerating" in q2.question_text
    assert "total distance" in q2.question_text
    assert q2.source_pages == [1, 2]
    assert "SPLIT_PAGE_CONTINUATION" in q2.warnings


def test_e2e_separate_answer_key_association():
    qp_path = SAMPLES_DIR / "sample_05_question_paper.pdf"
    ak_path = SAMPLES_DIR / "sample_06_separate_answer_key.pdf"

    # Extract Question Paper
    qp_pages = OCREngine.process_file(str(qp_path), "application/pdf")
    qp_data = [(p.page_number, p.text) for p in qp_pages]
    questions, _ = QuestionExtractor.extract_from_pages(qp_data)
    assert len(questions) == 3

    # Extract Standalone Answer Key
    ak_pages = OCREngine.process_file(str(ak_path), "application/pdf")
    ak_data = [(p.page_number, p.text) for p in ak_pages]
    _, answer_key = QuestionExtractor.extract_from_pages(ak_data)
    assert len(answer_key) >= 3

    # Reconcile
    db_questions = [
        Question(
            document_id=None,
            question_number=q.question_number,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            source_pages=q.source_pages,
        )
        for q in questions
    ]
    AnswerKeyService.match_answers(db_questions, answer_key, source=AnswerSource.RELATED_DOCUMENT)

    assert db_questions[0].detected_answer == "B"
    assert db_questions[0].answer_source == AnswerSource.RELATED_DOCUMENT
    assert db_questions[1].detected_answer == "B"
    assert db_questions[2].detected_answer == "A"
