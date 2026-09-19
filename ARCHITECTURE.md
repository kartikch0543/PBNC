# Document Intelligence & Question Extraction Service — Architecture Design Document

## 1. High-Level System Architecture

The service is structured as a **Modular Monolith with an Asynchronous Queue Worker**, designed for high throughput, predictable latency, and explainable intelligence extraction.

```
                                 ┌─────────────────────────────────┐
                                 │       Client / Reviewer UI      │
                                 │   (Dashboard, Swagger, Postman) │
                                 └────────────────┬────────────────┘
                                                  │
                                                  ▼
                                 ┌─────────────────────────────────┐
                                 │       FastAPI API Layer         │
                                 │  • OAuth2 / JWT Auth Gate       │
                                 │  • Magic-Byte MIME Validation   │
                                 │  • SHA-256 Storage Stream       │
                                 └──────┬──────────────────┬───────┘
                                        │                  │
                         Enqueues Job   │                  │ Persists Metadata
                                        ▼                  ▼
                         ┌────────────────────┐   ┌────────────────────┐
                         │   Redis Task Queue │   │ PostgreSQL DB      │
                         │   (ARQ Async Broker│   │ • users            │
                         └──────────────┬─────┘   │ • documents        │
                                        │         │ • processing_jobs  │
                                        ▼         │ • questions        │
                         ┌────────────────────┐   │ • relationships    │
                         │ Async Worker (ARQ) │   │ • warnings         │
                         └──────────────┬─────┘   └─────────▲──────────┘
                                        │                   │
                                        │ Updates Progress  │
                                        └───────────────────┘
```

---

## 2. Layered Extraction & OCR Strategy

Rather than naively piping entire multi-megabyte PDFs to external LLM APIs (which introduces unbounded cost, rate limiting, and hallucinated tokens), the system uses a **layered, progressive extraction funnel**:

```
[ Incoming File (PDF / PNG / JPEG) ]
                 │
                 ▼
    ┌───────────────────────────┐
    │ Native Text Density Check │ ── PyMuPDF (fitz) evaluates character density per page.
    └────────────┬──────────────┘
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
[ High Native Text ]   [ Low Native Text / Scan ]
       │                   │
       │                   ├── 1. Rasterize page to high-res image (144/300 DPI)
       │                   ├── 2. Multimodal Vision AI (Gemini Flash) with strict JSON schema
       │                   └── 3. Local Tesseract OCR fallback
       ▼                   ▼
┌──────────────────────────────────────────────┐
│ Deterministic Boundary Segmenter (extractor) │
│ • Multi-page continuity tracking             │
│ • Diverse numbering recognition              │
│ • Unnumbered question preservation           │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ Answer-Key Detection & Reconciliation Engine │
│ • Inline answer labels                       │
│ • Intra-document trailing answer keys        │
│ • Inter-document linked answer key papers    │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ Explainable Confidence Calculator            │
│ • Signal-weighted composite score (0.0 - 1.0)│
│ • Granular review warnings for human QA      │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ Atomic PostgreSQL Persistence                │
│ • Questions, Options (JSONB), Audit Warnings │
└──────────────────────────────────────────────┘
```

---

## 3. Core Intelligence Components

### 3.1. Question & Option Segmentation
- **Anchor Detection**: Dynamically parses question numbers using regex heuristics:
  - Standard numerals: `1.`, `2.`, `1)`, `2)`
  - Prefixed numerals: `Q1.`, `Q. 2`, `Question 3:`
  - Parenthesized numerals: `(1)`, `(2)`, `(3a)`
- **Unnumbered Questions**: If question text has no preceding number, the system preserves `question_number = null` and generates a `MISSING_QUESTION_NUMBER` warning. **It never fabricates question numbers.**
- **Multi-Page Spanning**: Questions split by page breaks are carried over in a stateful page buffer. The merged question retains all originating page numbers in `source_pages: [1, 2]` and flags `SPLIT_PAGE_CONTINUATION`.
- **Option Extraction**: Parses multiple choice keys (`A-D`, `(a)-(d)`, `(i)-(iv)`) into structured JSON items.

### 3.2. Answer-Key Association & Inter-Document Linking
- **Intra-Document**: Trailing or inline answer blocks are detected and mapped to question identifiers.
- **Inter-Document**: When a user links two documents (`POST /documents/{id}/relationships` with `relationship_type = "ANSWER_KEY_FOR"`), the background reconciliation service processes the target answer key and retroactively updates the source question paper's questions.
- **Unmatched State**: If an answer cannot be confidently associated, the system explicitly leaves `detected_answer = null`, assigns `answer_source = "UNMATCHED"`, and records an `UNMATCHED_ANSWER_KEY` warning.

### 3.3. Explainable Confidence Scoring Model
The system derives an objective, explainable score between `0.0` and `1.0`:
* Base starting score: `1.0`
* Missing question number penalty: `-0.25`
* Unusually short question stem (< 15 chars): `-0.30`
* Multiple choice with < 2 extracted options: `-0.35`
* Split across page breaks: `-0.05`
* Unmatched answer key: `-0.10`
* Low-resolution scanned page: `-0.10`

Questions are classified into:
* **`EXTRACTED`** (Score ≥ 0.80)
* **`REVIEW_REQUIRED`** (0.50 ≤ Score < 0.80)
* **`PARTIAL`** (Score < 0.50)

Every penalty attaches a traceable `ExtractionWarning` to the database, giving human reviewers immediate context for inspection.

---

## 4. Security & File Safety Design

1. **Path Traversal Defense**: Client-supplied filenames are sanitized using `os.path.basename` and stripped of null bytes (`\x00`) and invalid filesystem characters. Storage uses UUID-named files on disk.
2. **Magic Byte Verification**: Rather than trusting the client `Content-Type` header, file headers are sniffed for valid magic signatures:
   - PDF: `%PDF`
   - PNG: `\x89PNG\r\n\x1a\n`
   - JPEG: `\xff\xd8\xff`
   Any mismatched or spoofed file is immediately rejected with `400 Bad Request`.
3. **Data Integrity & Deduplication**: Every file streams through SHA-256 hashing during upload.
4. **Tenant Isolation**: Every database query on documents, jobs, questions, and warnings enforces ownership scoping against `current_user.id`.

---

## 5. Architectural Trade-offs & Limitations

| Decision | Trade-off Made | Why Chosen |
| :--- | :--- | :--- |
| **ARQ (Asyncio Worker) vs Celery** | Less third-party UI tooling (no Flower) | 100% native asyncio; shares the same SQLAlchemy engine and connection pool with FastAPI; zero Windows thread pool bugs. |
| **Hybrid Rules + Vision AI vs End-to-End LLM** | Requires rule-based heuristics | 10x faster execution; deterministic question numbering; zero cost for digital PDFs; resilient when external API quotas are exhausted. |
| **UUID Primary Keys vs Auto-increment Integers** | Slightly larger index size (16 bytes vs 8 bytes) | Non-guessable IDs; client-safe; eliminates enumeration attacks across multi-tenant documents. |
