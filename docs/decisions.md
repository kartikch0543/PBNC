# Architecture Decisions & Engineering Trade-Offs

This document records the key architectural, technical, and algorithmic decisions made in **DocuQ — Document Intelligence & Question Extraction Platform** to satisfy the Pragati Bharati Round 2 engineering requirements.

---

## 1. Document Extraction: PyMuPDF (`fitz`) vs. PDFMiner / PyPDF

### Context
The service must extract structured text, font attributes, and coordinates from diverse digital PDFs while also supporting scans.

### Decision
We chose **PyMuPDF (`fitz`)** over PDFMiner, PyPDF, and pdfplumber.

### Rationale & Trade-offs
- **Execution Speed**: PyMuPDF executes in C (`MuPDF`), processing a 10-page document in ~40ms compared to 800ms–2000ms with pure-Python PDFMiner.
- **Visual Rendering**: PyMuPDF renders high-DPI raster pixmaps (300 DPI) directly from PDF pages without requiring external binaries like `pdftoppm` or `poppler-utils`. This enables the side-by-side source verification feature in our reviewer workbench (`GET /documents/{id}/source/{page}`).
- **Memory Footprint**: Extremely low memory consumption under concurrent background tasks.
- **Trade-off**: Requires binary wheel installation (`pymupdf`), which is universally available on Windows, Linux, and macOS.

---

## 2. Async Task Queue: ARQ & Graceful In-Process Fallback vs. Celery

### Context
Document processing must happen asynchronously so the client is not blocked during upload.

### Decision
We implemented **ARQ (Async Redis Queue)** coupled with an automatic **in-process `asyncio.Task` fallback**.

### Rationale & Trade-offs
- **Windows Process-Forking Issues**: Celery has well-documented bugs on Windows with process pools (`billiard` and Windows `fork` limitations), frequently requiring workarounds (`--pool=solo` or gevent) that degrade production behavior.
- **Native AsyncIO Compatibility**: ARQ is built from the ground up for Python 3.11+ `asyncio`, aligning directly with FastAPI and SQLAlchemy async sessions.
- **Zero-Barrier Evaluation**: When evaluated on machines where Redis is not running locally, the application automatically executes background tasks via `asyncio.create_task` without crashing or blocking the HTTP response. When Redis is present, it queues tasks to Redis for distributed workers.

---

## 3. Database Persistence: Dual-Engine PostgreSQL with SQLite Auto-Fallback

### Context
The assignment requires PostgreSQL for persistence, but evaluation environments may not have a PostgreSQL daemon running locally.

### Decision
We engineered a dual-engine architecture in `app.core.database.py`:
- **Primary Engine**: PostgreSQL 16 via `asyncpg` for production.
- **Autonomous Fallback Engine**: `sqlite+aiosqlite` on `doc_intelligence.db` if the PostgreSQL connection is refused on startup.

### Rationale & Trade-offs
- The evaluation team can clone the repository and run `.\run_api.ps1` immediately without setting up databases or configuring passwords.
- Full relational integrity (foreign keys, cascading deletes, JSONB/JSON column mappings) is preserved across both database backends.

---

## 4. Optical Character Recognition (OCR) & AI Strategy

### Context
The system must support scanned PDFs, low-quality images, and rotated pages.

### Decision
We implemented a **two-tier heuristic + vision OCR strategy**:
1. **Tier 1 (Deterministic Fast Path)**: Inspect the text stream of each page. If character density exceeds 150 characters per page, extract digital text blocks directly with zero external API calls.
2. **Tier 2 (Vision Multimodal Fallback)**: If a page is a raster scan or has low text density, rasterize to 300 DPI and invoke the replaceable vision AI client (Google Gemini 2.0 Flash / 1.5 Flash) with strict JSON schema enforcement.

### Rationale & Trade-offs
- Eliminates unnecessary API costs and latency on clean digital PDFs.
- Never hardcodes API keys (configured via `GEMINI_API_KEY`).
- Works offline on digital PDFs even if no internet connection or AI key is supplied.

---

## 5. Question Numbering: Null Preservation vs. Guessing / Inventing

### Context
Unnumbered questions and varying formats (`1.`, `Q1.`, `1)`, `Question 1`) occur in practice.

### Decision
If a question anchor does not contain an explicit number:
- We store `question_number = null`.
- We assign an audit flag `UNNUMBERED_QUESTION`.
- We **never invent or guess fake numbers** (e.g. we do not fabricate "Question 5" when the original paper omitted it).

### Rationale & Trade-offs
- Preserves ground-truth fidelity.
- Allows the human reviewer to verify and assign numbers during review rather than correcting hallucinated data.

---

## 6. Multi-Page Question Reconstruction

### Context
Questions can begin near the bottom of Page $N$ and continue onto Page $N+1$.

### Decision
We check grammatical and layout continuity:
- If a question on Page $N$ ends with a colon, open parenthetical, or incomplete clause, and Page $N+1$ begins without a new question anchor, the text is assembled into a single logical question with `source_pages: [N, N+1]`.
- An audit flag `MULTI_PAGE_CONTINUATION` is created.

---

## 7. Explainable Confidence Scoring

### Context
Downstream assessment platforms need an indication of extraction reliability.

### Decision
We use a multi-factor composite scoring formula ($0.0$ to $1.0$):
$$\text{Confidence} = 0.35 \times S_{\text{boundary}} + 0.25 \times S_{\text{options}} + 0.25 \times S_{\text{answer}} + 0.15 \times S_{\text{continuity}}$$
- Categorized as:
  - `CONFIDENT` ($\ge 0.80$)
  - `REVIEW_REQUIRED` ($0.50 \le \text{Score} < 0.80$)
  - `PARTIAL` ($< 0.50$)
- Accompanied by explicit, human-readable warning messages explaining *why* the score was lowered.
