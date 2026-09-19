# Document Intelligence & Question Extraction Service
**Pragati Bharati Full Stack Developer — Round 2 Assignment**

A production-oriented, explainable backend service that converts multi-format, unstructured, and imperfect examination materials (digital PDFs, scans, images) into machine-readable, structured question-and-answer records.

---

## Key Features

- **Multi-Format Ingestion**: Supports digital PDFs, scanned PDFs, PNG, and JPEG images.
- **Asynchronous Processing**: Upload returns `HTTP 202 Accepted` immediately; documents process in the background via an asyncio worker (Redis + ARQ with graceful in-process fallback).
- **Intelligent Segmentation**: Robust parsing for diverse numbering formats (`1.`, `Q. 1`, `(1)`), multi-page question splits, and unnumbered questions without hallucinating numbers.
- **Answer-Key Reconciliation**: Detects inline answers, trailing answer keys, and links separate documents (e.g. `QuestionPaper.pdf` + `AnswerKey.pdf`).
- **Explainable Confidence Scoring**: Rule-weighted scoring (`0.0` - `1.0`) with actionable QA review warnings (`MISSING_QUESTION_NUMBER`, `SPLIT_PAGE_CONTINUATION`, `AMBIGUOUS_OPTIONS`).
- **Security by Design**: Magic-byte MIME sniffing, SHA-256 deduplication, path traversal protection, and JWT user scoping.
- **Minimal Human-Review Dashboard**: Lightweight built-in dashboard served at `http://localhost:8000` to inspect questions and confidence ratings.
- **Zero-Docker Native Python Architecture**: Runs directly on the host machine using standard Python virtual environments.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **API Framework** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL 16 (asyncpg + SQLAlchemy 2.0 async + Alembic) |
| **Async Worker & Queue** | Redis 7 + ARQ (Asyncio Redis Queue) |
| **Document Processing** | PyMuPDF (`fitz`), Pillow, pdf2image |
| **OCR & Vision AI** | Google Gemini 2.0 Flash (optional API key) + PyMuPDF / Tesseract fallback |
| **Authentication** | PyJWT + Bcrypt |
| **Testing** | pytest, pytest-asyncio, httpx |

---

## Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.11+ (Python 3.14/3.11 supported)
- Git
- PostgreSQL & Redis (running locally, or use SQLite/in-process mode for quick evaluation)

### 2. Virtual Environment & Dependencies
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
*(Optional: Provide a `GEMINI_API_KEY` in `.env` if you want to test cloud multimodal vision on scanned exams).*

### 4. Generate Sample Test Documents
```powershell
python scripts/generate_samples.py
```
This programmatically generates 7 test documents in `backend/samples/`:
1. `sample_01_clean.pdf` — Clean digital examination with multiple questions & trailing answer key.
2. `sample_02_scanned.pdf` — Scanned/rasterized PDF.
3. `sample_03_low_quality.png` — Image scan with questions.
4. `sample_04_multi_page_question.pdf` — Question 2 spans across Page 1 and Page 2.
5. `sample_05_question_paper.pdf` — Question paper without embedded answers.
6. `sample_06_separate_answer_key.pdf` — Standalone answer key to link with `sample_05`.
7. `sample_07_invalid.txt` — Invalid document to verify security rejection.

### 5. Running the Application
Open a terminal and run the API server:
```powershell
.\run_api.ps1
```
The server will start at: **`http://127.0.0.1:8000`**

Open another terminal to run the async background worker:
```powershell
.\run_worker.ps1
```

---

## Interactive Interfaces

- **Human Review Dashboard**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) to register, upload documents, monitor real-time processing status, and inspect questions with confidence badges and audit warnings.
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Automated Tests

Run the full test suite covering security, storage, question parsing, multi-page continuation, confidence scoring, and answer-key matching:
```powershell
.\run_tests.ps1
```
Or directly:
```powershell
pytest backend/tests -v
```

---

## Postman Collection

Import `docs/Document_Intelligence.postman_collection.json` into Postman. It includes pre-configured environment variables and test scripts covering:
1. User Registration & Login (automatically extracts JWT token)
2. Document Upload (`POST /documents/upload`)
3. Async Status Polling (`GET /documents/{id}/status`)
4. Structured Question Retrieval (`GET /documents/{id}/questions`)
5. Answer Key Summary (`GET /documents/{id}/answers`)
6. Audit Warnings (`GET /documents/{id}/warnings`)
7. Separate Document Relationship Linking (`POST /documents/{id}/relationships`)
8. Invalid Document Rejection Testing

---

## API Surface Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT token |
| `GET` | `/api/v1/auth/me` | Retrieve authenticated user profile |
| `POST` | `/api/v1/documents/upload` | Upload PDF/image (returns `202 Accepted`) |
| `GET` | `/api/v1/documents` | List uploaded documents |
| `GET` | `/api/v1/documents/{id}` | Get document metadata |
| `GET` | `/api/v1/documents/{id}/status` | Check async job processing progress |
| `GET` | `/api/v1/documents/{id}/questions` | Retrieve extracted structured questions |
| `GET` | `/api/v1/questions/{id}` | Retrieve individual question details |
| `GET` | `/api/v1/documents/{id}/answers` | Retrieve answers and match confidence |
| `GET` | `/api/v1/documents/{id}/warnings` | Retrieve QA review warnings for human review |
| `POST` | `/api/v1/documents/{id}/relationships`| Associate Question Paper with Answer Key |
| `GET` | `/api/v1/documents/{id}/relationships`| List document associations |

---

## Interview Defense & Key Design Decisions

### 1. Why FastAPI?
FastAPI provides native asynchronous execution (`asyncio`), automatic Pydantic request/response schema validation, OpenAPI generation, and exceptional throughput for I/O-bound document workloads.

### 2. Why a Layered Extraction Strategy instead of sending everything to an LLM?
Digital PDFs comprise >75% of academic question banks. Sending multi-page PDFs directly to vision models adds 5–15 seconds of latency, high API costs, and risks token hallucinations. Our fast-path PyMuPDF text engine extracts digital text in under 50ms with 100% fidelity. We invoke Multimodal Vision AI only for low-density scans and complex handwriting.

### 3. How do you handle unnumbered questions?
We explicitly set `question_number = null` and generate a `MISSING_QUESTION_NUMBER` review warning. We **never hallucinate or invent question numbers**, preserving data integrity for downstream assessment systems.

### 4. How do you handle questions spanning across pages?
Our extractor maintains a stateful continuation buffer across consecutive pages. If a page break occurs while an active question stem or option list is incomplete, the buffer carries over to the next page, merges the text, records `source_pages: [1, 2]`, and flags `SPLIT_PAGE_CONTINUATION`.

### 5. How are separate Question Papers and Answer Keys reconciled?
Through the `document_relationships` table (`relationship_type = 'ANSWER_KEY_FOR'`). Once linked, the service extracts the answer key from the target document and maps solutions to questions using normalized question numbering.
