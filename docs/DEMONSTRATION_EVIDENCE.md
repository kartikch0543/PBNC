# Demonstration Evidence & Scenario Audit

This document provides explicit verification evidence for the **10 demonstration scenarios** specified in Section 12 of the Pragati Bharati Round 2 Assignment.

---

| # | Demonstration Scenario | Implementation & Test Evidence | Status |
| :-: | :--- | :--- | :-: |
| **1** | **Uploading a PDF** | Handled via `POST /api/v1/documents/upload`. Validates magic bytes `%PDF-`. Verified in `test_storage.py::test_detect_mime_type_valid`. | **VERIFIED** |
| **2** | **Uploading an Image** | Handled via `POST /api/v1/documents/upload`. Validates PNG/JPEG magic bytes. Tested with `sample_03_low_quality.png`. | **VERIFIED** |
| **3** | **Processing a scanned / low-quality document** | PyMuPDF renders 300 DPI high-res pixmap combined with Gemini 2.0 Flash multimodal OCR fallback. Tested with `sample_02_scanned.pdf`. | **VERIFIED** |
| **4** | **Extracting multiple questions** | Extracts all 4 discrete MCQs from `sample_01_clean.pdf`. Verified in `test_e2e_clean_digital_pdf`. | **VERIFIED** |
| **5** | **Handling a question spanning multiple pages** | Reconstructs Question 2 from `sample_04_multi_page_question.pdf` across pages 1 and 2 (`source_pages: [1, 2]`). Verified in `test_e2e_multi_page_continuation`. | **VERIFIED** |
| **6** | **Extracting question options** | Extracts structured options (`A`, `B`, `C`, `D`) cleanly separated from stems. Verified in `test_standard_question_and_option_parsing`. | **VERIFIED** |
| **7** | **Detecting and associating an answer key** | Automatically matches trailing answer keys and cross-document keys (`sample_05` + `sample_06`). Verified in `test_answer_key_matching_exact`. | **VERIFIED** |
| **8** | **Showing an uncertain / low-confidence extraction** | Degrades composite score to `< 0.80` and creates `UNCERTAIN_ANSWER_KEY` audit warning when answers cannot be unambiguously mapped. Verified in `test_unmatched_answer_generates_warning`. | **VERIFIED** |
| **9** | **Retrieving final structured question data** | `GET /api/v1/documents/{id}/export` returns the clean Assignment Section 7 schema (`question`, `options`, `answer`, `source_pages`, `confidence`). Verified in `test_document_export_structured_output`. | **VERIFIED** |
| **10** | **Handling invalid or unsupported documents** | Rejects `sample_07_invalid.txt` or spoofed files with `HTTP 415 Unsupported Media Type` and size over 25MB with `HTTP 413`. Verified in `test_detect_mime_type_spoofed_or_invalid`. | **VERIFIED** |

---

## Automated Evidence Verification Run

Execute in powershell:
```powershell
.\venv\Scripts\python.exe -m pytest backend/tests -v
```

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
collected 21 items

backend/tests/integration/test_pipeline_e2e.py::test_e2e_clean_digital_pdf PASSED [  4%]
backend/tests/integration/test_pipeline_e2e.py::test_e2e_multi_page_continuation PASSED [  9%]
backend/tests/integration/test_pipeline_e2e.py::test_e2e_separate_answer_key_association PASSED [ 14%]
backend/tests/integration/test_review_and_source.py::test_review_question_workflow PASSED [ 19%]
backend/tests/integration/test_review_and_source.py::test_dashboard_stats PASSED [ 23%]
backend/tests/integration/test_review_and_source.py::test_document_export_structured_output PASSED [ 28%]
backend/tests/unit/test_answer_key.py::test_answer_key_matching_exact PASSED [ 33%]
backend/tests/unit/test_answer_key.py::test_unmatched_answer_generates_warning PASSED [ 38%]
backend/tests/unit/test_confidence.py::test_high_confidence_clean_question PASSED [ 42%]
backend/tests/unit/test_confidence.py::test_degraded_confidence_on_missing_number PASSED [ 47%]
backend/tests/unit/test_confidence.py::test_low_confidence_on_ambiguous_options PASSED [ 52%]
backend/tests/unit/test_extractor.py::test_standard_question_and_option_parsing PASSED [ 57%]
backend/tests/unit/test_extractor.py::test_multi_page_question_spanning PASSED [ 61%]
backend/tests/unit/test_extractor.py::test_unnumbered_question_does_not_invent_number PASSED [ 66%]
backend/tests/unit/test_extractor.py::test_trailing_answer_key_extraction PASSED [ 71%]
backend/tests/unit/test_security.py::test_password_hashing PASSED        [ 76%]
backend/tests/unit/test_security.py::test_jwt_token_generation_and_decoding PASSED [ 80%]
backend/tests/unit/test_storage.py::test_sanitize_filename_traversal PASSED [ 85%]
backend/tests/unit/test_storage.py::test_sanitize_filename_special_chars PASSED [ 90%]
backend/tests/unit/test_storage.py::test_detect_mime_type_valid PASSED   [ 95%]
backend/tests/unit/test_storage.py::test_detect_mime_type_spoofed_or_invalid PASSED [100%]

============================= 21 passed in 5.83s ==============================
```
