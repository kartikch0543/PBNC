"""
Generates representative sample test documents for all evaluation criteria:
1. sample_01_clean.pdf - Clean digital PDF with multiple questions & answer key
2. sample_02_scanned.pdf - Simulated scanned PDF (rasterized page image)
3. sample_03_low_quality.png - Image examination with noise
4. sample_04_multi_page_question.pdf - Question 2 splits across page 1 and page 2
5. sample_05_question_paper.pdf - Question paper with no answer key
6. sample_06_separate_answer_key.pdf - Standalone answer key to link with sample_05
"""
import os
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "backend" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_sample_01_clean():
    """Generates clean digital PDF with standard MCQs and Answer Key."""
    doc = fitz.open()
    page = doc.new_page()

    text = """GENERAL SCIENCE EXAMINATION — GRADE 10
Time: 60 Minutes                                 Total Marks: 50
----------------------------------------------------------------

1. What is the powerhouse of the eukaryotic cell?
   A. Nucleus
   B. Mitochondria
   C. Ribosome
   D. Endoplasmic Reticulum

Q. 2 Which gas is most abundant in Earth's atmosphere?
   (a) Oxygen
   (b) Carbon Dioxide
   (c) Nitrogen
   (d) Argon

3. What is the chemical formula for table salt?
   A. NaCl
   B. KCl
   C. CaCO3
   D. Na2SO4

4) Sound waves cannot travel through which of the following?
   A. Air
   B. Water
   C. Steel
   D. Vacuum

----------------------------------------------------------------
Answer Key:
1: B
2: C
3: A
4: D
"""
    page.insert_text((50, 50), text, fontsize=11, fontname="helv")
    doc.save(str(SAMPLES_DIR / "sample_01_clean.pdf"))
    doc.close()
    print("Generated sample_01_clean.pdf")


def generate_sample_04_multi_page():
    """Generates a 2-page PDF where Question 2 spans across Page 1 and Page 2."""
    doc = fitz.open()

    # Page 1
    page1 = doc.new_page()
    text_p1 = """PHYSICS MIDTERM EXAMINATION
================================================================

1. State the SI unit of electric current.
   A. Volt
   B. Ampere
   C. Ohm
   D. Watt

2. A high-speed train travels along a straight track, accelerating
   uniformly from an initial velocity of 15 m/s to 45 m/s over
   a time interval of 10 seconds.
"""
    page1.insert_text((50, 50), text_p1, fontsize=12, fontname="helv")

    # Page 2
    page2 = doc.new_page()
    text_p2 = """   Determine the total distance traversed by the train during this
   acceleration phase, assuming linear motion throughout.
   (A) 150 meters
   (B) 300 meters
   (C) 450 meters
   (D) 600 meters

3. Which law explains the recoil of a fired rifle?
   A. Newton's First Law
   B. Newton's Second Law
   C. Newton's Third Law
   D. Law of Universal Gravitation

----------------------------------------------------------------
Solutions:
1. B
2. B
3. C
"""
    page2.insert_text((50, 50), text_p2, fontsize=12, fontname="helv")
    doc.save(str(SAMPLES_DIR / "sample_04_multi_page_question.pdf"))
    doc.close()
    print("Generated sample_04_multi_page_question.pdf")


def generate_sample_05_and_06():
    """Generates QuestionPaper.pdf and separate AnswerKey.pdf for relationship testing."""
    # Question Paper
    doc_qp = fitz.open()
    page_qp = doc_qp.new_page()
    text_qp = """CHEMISTRY ENTRANCE TEST — PAPER A
================================================================

1. What is the pH of pure water at 25 degrees Celsius?
   A. 5
   B. 7
   C. 9
   D. 14

2. Which element has the atomic number 6?
   A. Boron
   B. Carbon
   C. Nitrogen
   D. Oxygen

3. Bronze is an alloy primarily composed of copper and:
   A. Tin
   B. Zinc
   C. Nickel
   D. Aluminum
"""
    page_qp.insert_text((50, 50), text_qp, fontsize=12, fontname="helv")
    doc_qp.save(str(SAMPLES_DIR / "sample_05_question_paper.pdf"))
    doc_qp.close()
    print("Generated sample_05_question_paper.pdf")

    # Standalone Answer Key
    doc_ak = fitz.open()
    page_ak = doc_ak.new_page()
    text_ak = """OFFICIAL ANSWER KEY — CHEMISTRY PAPER A
================================================================
Paper Code: CHEM-A-2026

Answer Key:
1: B
2: B
3: A
"""
    page_ak.insert_text((50, 50), text_ak, fontsize=12, fontname="helv")
    doc_ak.save(str(SAMPLES_DIR / "sample_06_separate_answer_key.pdf"))
    doc_ak.close()
    print("Generated sample_06_separate_answer_key.pdf")


def generate_sample_03_image():
    """Generates a PNG image containing questions."""
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    lines = [
        "COMPUTER SCIENCE QUIZ",
        "--------------------------------------------------",
        "1. Which data structure uses LIFO (Last In First Out)?",
        "   A. Queue",
        "   B. Stack",
        "   C. Array",
        "   D. Tree",
        "",
        "2. What does HTTP stand for in networking?",
        "   A. HyperText Transfer Protocol",
        "   B. High Traffic Transfer Protocol",
        "   C. Hyperlink Text Telecommunication Program",
        "",
        "Answers:",
        "1. B",
        "2. A",
    ]

    y = 30
    for line in lines:
        draw.text((40, y), line, fill=(0, 0, 0))
        y += 28

    img.save(str(SAMPLES_DIR / "sample_03_low_quality.png"))
    print("Generated sample_03_low_quality.png")


def generate_sample_02_scanned():
    """Generates a scanned PDF by converting sample_03_low_quality image into a rasterized PDF page."""
    img_path = SAMPLES_DIR / "sample_03_low_quality.png"
    img = Image.open(img_path)
    pdf_path = SAMPLES_DIR / "sample_02_scanned.pdf"
    img.save(str(pdf_path), "PDF", resolution=100.0)
    print("Generated sample_02_scanned.pdf")


if __name__ == "__main__":
    generate_sample_01_clean()
    generate_sample_04_multi_page()
    generate_sample_05_and_06()
    generate_sample_03_image()
    generate_sample_02_scanned()
    print("All sample test documents generated successfully!")
