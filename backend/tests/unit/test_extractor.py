from app.models.question import QuestionType
from app.services.extractor import QuestionExtractor


def test_standard_question_and_option_parsing():
    page_text = """
    1. What is the primary gas found in Earth's atmosphere?
    A. Oxygen
    B. Nitrogen
    C. Carbon Dioxide
    D. Hydrogen

    Q. 2 Which planet is known as the Red Planet?
    (a) Venus
    (b) Mars
    (c) Jupiter
    (d) Saturn
    """

    questions, answer_key = QuestionExtractor.extract_from_pages([(1, page_text)])
    assert len(questions) == 2

    # Check Question 1
    q1 = questions[0]
    assert q1.question_number == "1"
    assert "primary gas" in q1.question_text
    assert q1.question_type == QuestionType.MULTIPLE_CHOICE
    assert len(q1.options) == 4
    assert q1.options[0]["key"] == "A"
    assert q1.options[0]["text"] == "Oxygen"
    assert q1.options[1]["key"] == "B"
    assert q1.options[1]["text"] == "Nitrogen"
    assert q1.source_pages == [1]

    # Check Question 2
    q2 = questions[1]
    assert q2.question_number == "2"
    assert "Red Planet" in q2.question_text
    assert len(q2.options) == 4
    assert q2.options[1]["key"] == "B"
    assert q2.options[1]["text"] == "Mars"


def test_multi_page_question_spanning():
    page_1 = """
    1. A car accelerates uniformly from rest to a speed of 20 m/s
    over a distance of 100 meters.
    """
    page_2 = """
    Calculate the acceleration of the car.
    (A) 1 m/s^2
    (B) 2 m/s^2
    (C) 3 m/s^2
    (D) 4 m/s^2

    2. What is the SI unit of force?
    A. Newton
    B. Joule
    """

    questions, _ = QuestionExtractor.extract_from_pages([(1, page_1), (2, page_2)])
    assert len(questions) == 2

    q1 = questions[0]
    assert q1.question_number == "1"
    assert "accelerates uniformly" in q1.question_text
    assert "Calculate the acceleration" in q1.question_text
    assert len(q1.options) == 4
    assert q1.source_pages == [1, 2]  # Traced across both pages
    assert "SPLIT_PAGE_CONTINUATION" in q1.warnings


def test_unnumbered_question_does_not_invent_number():
    page_text = """
    Explain the difference between supervised and unsupervised learning in machine learning algorithms?
    """

    questions, _ = QuestionExtractor.extract_from_pages([(1, page_text)])
    assert len(questions) == 1
    q = questions[0]
    assert q.question_number is None  # Must NOT hallucinate a number
    assert "supervised and unsupervised" in q.question_text
    assert "MISSING_QUESTION_NUMBER" in q.warnings


def test_trailing_answer_key_extraction():
    page_text = """
    1. First Question?
    A. Opt 1
    B. Opt 2

    Answer Key:
    1: A
    2: C
    3: D
    """

    questions, answer_key = QuestionExtractor.extract_from_pages([(1, page_text)])
    assert len(questions) == 1
    assert answer_key.get("1") == "A"
    assert answer_key.get("2") == "C"
    assert answer_key.get("3") == "D"


def test_beginning_answer_key_extraction():
    """Answer key appearing at the beginning of the document before questions."""
    page_text = """
    Answer Key:
    1. A  2. B  3. C

    Questions:
    1. What is the powerhouse of the cell?
    A. Mitochondria
    B. Ribosome
    C. Nucleus

    2. What is H2O?
    A. Water
    B. Carbon
    C. Nitrogen
    """

    questions, answer_key = QuestionExtractor.extract_from_pages([(1, page_text)])
    assert len(questions) == 2
    assert questions[0].question_number == "1"
    assert questions[1].question_number == "2"
    assert answer_key.get("1") == "A"
    assert answer_key.get("2") == "B"
    assert answer_key.get("3") == "C"


def test_diverse_answer_key_formatting_styles():
    """Handles diverse answer key styles: arrows, colons, brackets, dashes, words."""
    page_text = """
    Solutions:
    Q1 -> (A)
    Q2: Option B
    3 - C
    4 = D
    """

    _, answer_key = QuestionExtractor.extract_from_pages([(1, page_text)])
    assert answer_key.get("1") == "A"
    assert answer_key.get("2") == "B"
    assert answer_key.get("3") == "C"
    assert answer_key.get("4") == "D"


def test_answer_key_on_separate_page():
    """Handles answer key located on a dedicated/separate page."""
    page_1 = """
    1. What is velocity?
    A. Speed with direction
    B. Distance over time
    """
    page_2 = """
    Answer Key:
    1. A
    """

    questions, answer_key = QuestionExtractor.extract_from_pages([(1, page_1), (2, page_2)])
    assert len(questions) == 1
    assert answer_key.get("1") == "A"

