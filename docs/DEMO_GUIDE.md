# Demonstration Guide: 10 Assignment Scenarios
**Pragati Bharati Full Stack Developer — Round 2**

This guide outlines the exact demonstration procedure for all 10 mandatory evaluation scenarios specified in **Section 12 of the Assignment**.

---

## Prerequisites
Ensure the API server is running:
```powershell
.\run_api.ps1
```
URL: `http://127.0.0.1:8000`

---

## Scenario 1: Upload a PDF
- **Action**: In the Review Dashboard or via Postman/curl, upload `backend/samples/sample_01_clean.pdf`.
- **Expected API Response**: `HTTP 202 Accepted` with `document_id`, `job_id`, and status `PENDING`.
- **Evaluator Observation**: The upload finishes in milliseconds without blocking the client.

## Scenario 2: Upload an Image
- **Action**: Upload `backend/samples/sample_03_low_quality.png` (MIME: `image/png`).
- **Expected API Response**: `HTTP 202 Accepted`.
- **Evaluator Observation**: The service validates PNG magic bytes (`\x89PNG\r\n\x1a\n`) and processes the image as a single-page document.

## Scenario 3: Process Scanned / Low-Quality Document
- **Action**: Upload `backend/samples/sample_02_scanned.pdf`.
- **Expected Processing**: PyMuPDF detects low native character density and activates page rasterization at high DPI. If Gemini API key is configured, invokes multimodal vision; otherwise executes OCR fallback.
- **Evaluator Observation**: System extracts text and tags low OCR quality with a small confidence deduction (`-0.10`) rather than crashing.

## Scenario 4: Extract Multiple Questions
- **Action**: View extracted questions for `sample_01_clean.pdf`:
  `GET /api/v1/documents/{document_id}/questions`
- **Expected API Response**: Returns all 4 questions with question stems, question numbers (`1`, `2`, `3`, `4`), and classified question types (`MULTIPLE_CHOICE`).
- **Evaluator Observation**: Clean separation between question stems and answer keys.

## Scenario 5: Handle a Question Spanning Multiple Pages
- **Action**: Upload `backend/samples/sample_04_multi_page_question.pdf` and retrieve questions.
- **Expected API Response**: Question 2 contains the stem started on Page 1 ("A high-speed train travels along a straight track...") and finished on Page 2 ("Determine the total distance..."), with:
  ```json
  "source_pages": [1, 2]
  ```
- **Evaluator Observation**: Question 2 is unified into a single record with audit flag `SPLIT_PAGE_CONTINUATION`.

## Scenario 6: Extract Question Options
- **Action**: Inspect `options` array on any extracted multiple choice question.
- **Expected API Response**: Structured list:
  ```json
  "options": [
    { "key": "A", "text": "Nucleus" },
    { "key": "B", "text": "Mitochondria" },
    { "key": "C", "text": "Ribosome" },
    { "key": "D", "text": "Endoplasmic Reticulum" }
  ]
  ```
- **Evaluator Observation**: Keys and text are parsed into system-independent JSON objects, supporting both `A.` and `(a)` formats.

## Scenario 7: Detect and Associate an Answer Key
- **Action 7A (Intra-Document)**: In `sample_01_clean.pdf`, the trailing "Answer Key:" section maps `1 -> B`, `2 -> C`, `3 -> A`, `4 -> D`. In the API, `detected_answer` reflects `B`, `C`, `A`, `D` with `answer_source: "DOCUMENT_END"`.
- **Action 7B (Separate Document Relationship)**: Upload `sample_05_question_paper.pdf` and `sample_06_separate_answer_key.pdf`. Link them via:
  `POST /api/v1/documents/{qp_id}/relationships` with `{"target_document_id": "{ak_id}", "relationship_type": "ANSWER_KEY_FOR"}`.
- **Evaluator Observation**: The service parses the separate answer key and retroactively reconciles answers on the question paper with `answer_source: "RELATED_DOCUMENT"`.

## Scenario 8: Show an Uncertain / Low-Confidence Extraction
- **Action**: Query `GET /api/v1/documents/{id}/warnings`.
- **Expected API Response**: For an unnumbered question or an ambiguous question with fewer than 2 options:
  - Confidence drops to `< 0.80` (status: `REVIEW_REQUIRED` or `PARTIAL`).
  - Warning recorded: `MISSING_QUESTION_NUMBER` or `AMBIGUOUS_OPTIONS`.
- **Evaluator Observation**: Transparent, explainable scoring rationale rather than an opaque black-box number.

## Scenario 9: Retrieve the Final Structured Question Data
- **Action**: Query `GET /api/v1/documents/{id}/questions` or individual question `GET /api/v1/questions/{id}`.
- **Expected API Response**: Strict conformance with Section 7 of the assignment:
  ```json
  {
    "question": "What is the powerhouse of the eukaryotic cell?",
    "options": [...],
    "answer": "B",
    "source_pages": [1],
    "confidence": 1.0
  }
  ```
- **Evaluator Observation**: Format is decoupled from any frontend and immediately consumable by downstream examination engines.

## Scenario 10: Reject Invalid / Unsupported Document
- **Action**: Attempt to upload `backend/samples/sample_07_invalid.txt` or an executable disguised as `.pdf`.
- **Expected API Response**: `HTTP 400 Bad Request` with structured error:
  ```json
  {
    "error": {
      "code": "FILE_VALIDATION_ERROR",
      "message": "Unsupported file extension '.txt'. Allowed extensions: .pdf, .png, .jpg, .jpeg"
    }
  }
  ```
- **Evaluator Observation**: Security gate validates extension and magic header bytes before saving or processing.
