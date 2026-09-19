# DocuQ — 5 to 10 Minute Live Demonstration Script

This guide outlines the recommended live demonstration flow for evaluators and interviewers reviewing the **DocuQ Document Intelligence & Question Extraction Service**.

---

## Prerequisites (30 Seconds)

Ensure the service is running locally:
```powershell
# Option A: Native Execution (Recommended)
.\run_api.ps1
```
The application will be accessible at:
- **Web SaaS Interface**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Step 1: Authentication & Dashboard Overview (1 Minute)

1. Navigate to `http://127.0.0.1:8000/`.
2. Click **⚡ Quick Auto-Fill Demo Reviewer Credentials** (`evaluator@pragatibharati.org`).
3. Click **Sign In**.
4. Observe the **Intelligence Dashboard**:
   - 4 KPI Metric Cards: Total Documents, Total Questions, Review Required, Failed Jobs.
   - Recent Processing Jobs table with status badges and question counts.

---

## Step 2: Ingesting a Clean Digital PDF (1 Minute)

1. Click **+ Create Processing Job** in the top navigation.
2. Under **"1-Click Curated Test Samples"**, click **`Clean PDF (4 Qs)`**.
   - Notice the Question Paper dropzone auto-populates with `sample_01_clean.pdf`.
3. Click **Start Asynchronous Processing Pipeline**.
4. Observe the **Real-Time Processing Screen**:
   - The stage tracker progresses step-by-step through:
     `✓ File Validated` $\rightarrow$ `✓ Document Stored` $\rightarrow$ `✓ Text Extraction` $\rightarrow$ `✓ Detecting Boundaries` $\rightarrow$ `✓ Matching Answers` $\rightarrow$ `✓ Calculating Confidence`.
   - Discovered questions counter increments to **4**.
5. When complete, click **Inspect Extracted Questions & Review Queue**.

---

## Step 3: Question Extraction & Answer Matching (1 Minute)

1. On the **Results Page**:
   - Notice questions Q1, Q2, Q3, Q4.
   - Each option A, B, C, D is neatly segmented.
   - The correct answer is automatically highlighted in green with a `✓ Answer` badge based on the trailing answer key in the document.
   - All 4 questions show `98% Confidence`.

---

## Step 4: Multi-Page Question Spanning (1.5 Minutes)

1. Click **+ Create Job** in the navbar.
2. Click the sample button **`Multi-Page Q2 Test`** (`sample_04_multi_page_question.pdf`).
3. Click **Start Processing**.
4. Once completed, inspect **Question 2**:
   - Notice the badge: `Page(s): 1, 2`.
   - The question began at the bottom of Page 1 (*"Which sorting algorithm exhibits the following characteristics..."*) and seamlessly continued onto Page 2 without being cut in half.
   - An explainable audit warning is displayed: `[MULTI_PAGE_CONTINUATION] Question stem spans across pages 1 and 2`.

---

## Step 5: Side-by-Side Reviewer Workbench & Source Verification (1.5 Minutes)

1. On any question card, click **Review / Source**.
2. Observe the **Side-by-Side Workbench**:
   - **Left Column**: The editable human correction form (stem, options, correct answer, reviewer notes).
   - **Right Column**: The high-DPI rendered image of the exact source page from the PDF (`/api/v1/documents/{id}/source/{page}`).
3. Change the Question text or option text, add a note: *"Audited against original paper"*, and click **Save Correction & Mark Reviewed**.
4. Notice the green `✓ Manually Reviewed` badge appears on the card.
5. In PostgreSQL/SQLite, the `original_extraction` column immutably preserves the raw state for audit logs.

---

## Step 6: Separate Answer Key Cross-Document Linking (1 Minute)

1. Click **+ Create Job**.
2. Click **`Unanswered Paper`** (`sample_05_question_paper.pdf`).
3. Click **`+ Attach Separate Key`** (`sample_06_separate_answer_key.pdf`).
4. Click **Start Processing**.
5. Observe how the system reconciles the two separate documents, linking the answers from the second file to the questions in the first file.

---

## Step 7: Exporting Assignment Section 7 Structured Output (30 Seconds)

1. At the top of the Results page, click **`{ } Structured JSON (Sec 7)`**.
2. Inspect the machine-readable output:
```json
[
  {
    "question": "Which protocol is used for secure communication over the computer network?",
    "options": ["HTTP", "HTTPS", "FTP", "SMTP"],
    "answer": "B",
    "source_pages": [1],
    "confidence": 0.98
  }
]
```
3. Click **Copy JSON** to copy the payload.

---

## Step 8: Security & Invalid Document Rejection (30 Seconds)

1. Attempt to upload `backend/samples/sample_07_invalid.txt` or a spoofed `.txt` file.
2. The system checks magic bytes, rejects the file with `HTTP 415 Unsupported Media Type`, and refuses execution.

---

## Step 9: Running Automated Tests (1 Minute)

In your terminal, execute:
```powershell
.\venv\Scripts\python.exe -m pytest backend/tests -v
```
**Result**: 21 passed in ~5 seconds (100% passing, 0 warnings).
