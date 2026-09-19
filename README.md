# DocuQ — Document Intelligence & Question Extraction Platform
**Pragati Bharati Full Stack Developer — Round 2 Assignment**

[![GitHub Repository](https://img.shields.io/badge/GitHub-kartikch0543%2FPBNC-blue?logo=github)](https://github.com/kartikch0543/PBNC)
[![Tests](https://img.shields.io/badge/pytest-26%20passed-brightgreen)](https://github.com/kartikch0543/PBNC)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776ab?logo=python)](https://python.org)

**Repository Link**: [https://github.com/kartikch0543/PBNC](https://github.com/kartikch0543/PBNC)  
*(Also saved in project root as `GITHUB_REPO.txt` and `repo.txt`)*

---

## 📌 Executive Overview

**DocuQ** is a production-grade Document Intelligence & Question Extraction platform designed to ingest multi-format, unstructured, and imperfect examination materials (digital PDFs, scans, images) and transform them into clean, structured, machine-readable question banks for downstream assessment platforms.

The solution features:
1. **High-Performance FastAPI Backend**: Async pipeline, PyMuPDF vector text extraction, Tesseract OCR / Multimodal Vision AI fallback, ARQ/Redis asynchronous queuing, and explainable rule-weighted confidence scoring.
2. **Modern React 18 + Tailwind SaaS Frontend**: Complete with 1-Click Curated Test Sample evaluation, real-time stage progress tracker, Question Detail inspector, Section 7 JSON Exporter, and a **Side-by-Side Human Reviewer Workbench** featuring high-DPI original source page rendering.
3. **Multi-Document Relationship Reconciliation**: Cross-document linking (`Question Paper.pdf` + `Answer Key.pdf`) with automated answer mapping and option validation safeguards to prevent silent assignment of invalid answers.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.11+** (Python 3.11–3.14 supported)
- **Node.js 18+** (Optional — pre-compiled production UI bundle is already bundled and served directly by the backend at `http://127.0.0.1:8000/`)

### 2. Zero-Docker Native Python Setup (Windows / Linux / macOS)
```powershell
# 1. Clone repository
git clone https://github.com/kartikch0543/PBNC.git
cd PBNC

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Linux/macOS: source venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env

# 5. Start API Server (serves both API & modern React UI on port 8000)
.\run_api.ps1                 # Or: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **`http://127.0.0.1:8000`** in your browser:
- Click **"Fill Admin Demo Credentials"** $\to$ **"Sign In to DocuQ"**.
- Head to **"+ Create Job"** and use any of the **1-Click Curated Test Sample** buttons to run instant end-to-end evaluations.

### 3. Docker Container Execution
```bash
# Build and run with Docker Compose
docker-compose up --build
```
The application will be accessible at `http://localhost:8000`.

---

## 🧪 Automated Testing

DocuQ includes 26 comprehensive unit and end-to-end integration tests covering storage security, MIME sniffing, boundary segmentation, multi-page continuation, trailing/beginning/standalone answer key parsing, option reliability validation, reviewer audit trails, and Section 7 structured JSON export:

```powershell
# Run the complete test suite
.\venv\Scripts\python.exe -m pytest backend/tests -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
collected 26 items

backend/tests/integration/test_pipeline_e2e.py::test_e2e_clean_digital_pdf PASSED [  3%]
backend/tests/integration/test_pipeline_e2e.py::test_e2e_multi_page_continuation PASSED [  7%]
backend/tests/integration/test_pipeline_e2e.py::test_e2e_separate_answer_key_association PASSED [ 11%]
backend/tests/integration/test_review_and_source.py::test_review_question_workflow PASSED [ 15%]
backend/tests/integration/test_review_and_source.py::test_dashboard_stats PASSED [ 19%]
backend/tests/integration/test_review_and_source.py::test_document_export_structured_output PASSED [ 23%]
backend/tests/unit/test_answer_key.py::test_answer_key_matching_exact PASSED [ 26%]
backend/tests/unit/test_answer_key.py::test_invalid_option_in_answer_key_not_silently_assigned PASSED [ 30%]
backend/tests/unit/test_answer_key.py::test_answer_key_numeric_style_mapping PASSED [ 34%]
backend/tests/unit/test_answer_key.py::test_unmatched_answer_generates_warning PASSED [ 38%]
backend/tests/unit/test_confidence.py::test_high_confidence_clean_question PASSED [ 42%]
backend/tests/unit/test_confidence.py::test_degraded_confidence_on_missing_number PASSED [ 46%]
backend/tests/unit/test_confidence.py::test_low_confidence_on_ambiguous_options PASSED [ 50%]
backend/tests/unit/test_extractor.py::test_standard_question_and_option_parsing PASSED [ 53%]
backend/tests/unit/test_extractor.py::test_multi_page_question_spanning PASSED [ 57%]
backend/tests/unit/test_extractor.py::test_unnumbered_question_does_not_invent_number PASSED [ 61%]
backend/tests/unit/test_extractor.py::test_trailing_answer_key_extraction PASSED [ 65%]
backend/tests/unit/test_extractor.py::test_beginning_answer_key_extraction PASSED [ 69%]
backend/tests/unit/test_extractor.py::test_diverse_answer_key_formatting_styles PASSED [ 73%]
backend/tests/unit/test_extractor.py::test_answer_key_on_separate_page PASSED [ 76%]
backend/tests/unit/test_security.py::test_password_hashing PASSED        [ 80%]
backend/tests/unit/test_security.py::test_jwt_token_generation_and_decoding PASSED [ 84%]
backend/tests/unit/test_storage.py::test_sanitize_filename_traversal PASSED [ 88%]
backend/tests/unit/test_storage.py::test_sanitize_filename_special_chars PASSED [ 92%]
backend/tests/unit/test_storage.py::test_detect_mime_type_valid PASSED   [ 96%]
backend/tests/unit/test_storage.py::test_detect_mime_type_spoofed_or_invalid PASSED [100%]

============================= 26 passed in 5.74s ==============================
```

---

## 📋 Section 12: 10 Demonstration Scenarios

| # | Scenario | Sample Document | Verification Mechanism | Status |
| :-: | :--- | :--- | :--- | :-: |
| **1** | **Uploading a PDF** | `sample_01_clean.pdf` | Validates `%PDF-` magic bytes; returns `HTTP 202 Accepted` with async `job_id`. | **VERIFIED** |
| **2** | **Uploading an Image** | `sample_03_low_quality.png` | Validates PNG header; routes image raster through OCR ingestion. | **VERIFIED** |
| **3** | **Processing Scanned / Low-Quality Document** | `sample_02_scanned.pdf` | Dynamic 300 DPI raster rendering with OCR fallback; logs `LOW_SCAN_QUALITY`. | **VERIFIED** |
| **4** | **Extracting Multiple Questions** | `sample_01_clean.pdf` | Cleanly isolates Questions 1–4 into discrete database entities. | **VERIFIED** |
| **5** | **Handling Multi-Page Question Spanning** | `sample_04_multi_page_question.pdf` | Question 2 stem starts on Page 1 and concludes on Page 2; records `source_pages=[1, 2]` with `SPLIT_PAGE_CONTINUATION`. | **VERIFIED** |
| **6** | **Extracting Question Options** | `sample_01_clean.pdf` | Parses options `A`, `B`, `C`, `D` with full text preserved into structured JSON arrays. | **VERIFIED** |
| **7** | **Detecting & Associating Answer Key** | `sample_01_clean.pdf` | Parses trailing answer key table and binds answers to questions with `AnswerSource.DOCUMENT_END`. | **VERIFIED** |
| **8** | **Uncertain / Low-Confidence Extraction** | `sample_04_multi_page_question.pdf` | Multi-page span + OCR degradation deducts confidence score to $<0.80$, routing item to `REVIEW_REQUIRED`. | **VERIFIED** |
| **9** | **Retrieving Final Structured Question Data** | `GET /api/v1/documents/{id}/export` | Returns clean, system-independent JSON output adhering strictly to Section 7. | **VERIFIED** |
| **10**| **Handling Invalid / Unsupported Document** | `sample_07_invalid.txt` | Magic-byte validator rejects invalid text file uploaded as exam paper with `HTTP 400 Bad Request`. | **VERIFIED** |

---

## 🌐 Complete API Surface

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT bearer token |
| `GET` | `/api/v1/auth/me` | Retrieve authenticated user profile |
| `GET` | `/api/v1/dashboard/stats` | Retrieve platform KPIs, review queues, and recent jobs |
| `POST` | `/api/v1/documents/upload` | Upload PDF or image document (returns `HTTP 202 Accepted`) |
| `GET` | `/api/v1/documents` | List uploaded documents for user |
| `GET` | `/api/v1/documents/{id}` | Get document metadata |
| `GET` | `/api/v1/documents/{id}/status` | Poll asynchronous processing step & progress |
| `GET` | `/api/v1/documents/{id}/questions` | Retrieve extracted structured questions with filters |
| `GET` | `/api/v1/questions/{id}` | Retrieve individual question details |
| `PATCH`| `/api/v1/questions/{id}/review` | Submit human reviewer corrections with full audit trail |
| `GET` | `/api/v1/documents/{id}/source/{page}` | Render high-DPI page preview for visual verification |
| `GET` | `/api/v1/documents/{id}/export` | Export Section 7 structured JSON |
| `GET` | `/api/v1/documents/{id}/answers` | Retrieve answer mappings and sources |
| `GET` | `/api/v1/documents/{id}/warnings` | Retrieve QA extraction warnings |
| `POST` | `/api/v1/documents/{id}/relationships` | Link related documents (e.g. Question Paper + Answer Key) |
| `GET` | `/api/v1/documents/{id}/relationships` | List document relationships |
| `GET` | `/api/v1/documents/samples/{filename}` | Download pre-generated curated test samples |

Interactive OpenAPI documentation is live at **`http://127.0.0.1:8000/docs`** and ReDoc at **`http://127.0.0.1:8000/redoc`**.

---

## 📦 Required Deliverables Manifest

All 10 assignment deliverables are fully implemented and verified in the repository:

1. **Complete Source Code**: Fully modularized in `backend/` and `frontend/`.
2. **Database Migrations & Schema**: SQLAlchemy 2.0 async models in `backend/app/models/` and initialization scripts in `backend/app/core/database.py`.
3. **Sample Input Documents**: 7 test documents located in `backend/samples/`.
4. **Sample Extracted Output**: Full structured JSON in `docs/sample_extracted_output.json`.
5. **Setup Instructions**: Comprehensive instructions provided above and in `README.md`.
6. **Architecture Documentation**: Complete architecture guide in `ARCHITECTURE.md`, `docs/architecture.md`, and architectural decision records in `docs/decisions.md`.
7. **Automated Tests**: 26 automated unit and integration tests passing in `backend/tests/`.
8. **Postman Collection**: Fully configured collection in `docs/Document_Intelligence.postman_collection.json`.
9. **Swagger UI / OpenAPI Documentation**: Accessible at `/docs` and `/openapi.json`.
10. **Demonstration Evidence**: Detailed scenario evidence in `docs/DEMONSTRATION_EVIDENCE.md` and `docs/demo.md`.

---

## 🔒 Security & Compliance

- **Magic-Byte Sniffing**: Header inspection prevents file extension spoofing (`.exe` renamed to `.pdf` is rejected).
- **Path Traversal Protection**: Uploaded filenames are sanitized via `secure_filename` and stored with unique UUID prefixes.
- **Tenant Data Isolation**: Every SQL query is parameterized and scoped to `current_user.id`.
- **Zero Hallucination Guarantee**: Unnumbered questions remain `question_number = null`. Ambiguous answer keys raise warnings rather than silently guessing.
