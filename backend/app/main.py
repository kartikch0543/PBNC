import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import AppError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("document_intelligence")

app = FastAPI(
    title="Document Intelligence & Question Extraction Service",
    description=(
        "Production-oriented service converting unstructured multi-format examination papers "
        "and question banks (PDFs, scans, images) into structured machine-readable questions with "
        "explainable confidence and answer-key reconciliation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "extra": exc.extra,
            }
        },
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Service health and environment status endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "api_v1": settings.API_V1_STR,
    }


# Include v1 API routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# Minimal Human Review Dashboard (Lightweight Single-Page Interface)
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_review_dashboard():
    """Serves the minimal human-review and document inspection dashboard."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Intelligence — Review Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --primary: #38bdf8;
            --primary-hover: #0284c7;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 2rem; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
        h1 { font-size: 1.5rem; font-weight: 700; color: var(--primary); }
        .links a { color: var(--text-muted); text-decoration: none; margin-left: 1.5rem; font-size: 0.9rem; }
        .links a:hover { color: var(--primary); }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }
        .card-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.4rem; }
        input, select { width: 100%; padding: 0.6rem; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--text); }
        button { background: var(--primary); color: #000; font-weight: 600; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; transition: 0.2s; }
        button:hover { background: var(--primary-hover); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        .badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .badge-success { background: rgba(34, 197, 94, 0.2); color: var(--success); }
        .badge-warning { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
        .badge-danger { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
        .question-box { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }
        .option-item { font-size: 0.9rem; margin-top: 0.3rem; padding-left: 0.5rem; }
        .option-correct { color: var(--success); font-weight: 600; }
        .warning-box { background: rgba(245, 158, 11, 0.1); border-left: 3px solid var(--warning); padding: 0.5rem 1rem; margin-top: 0.5rem; font-size: 0.8rem; color: #fde68a; }
        pre { background: #000; padding: 0.8rem; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Document Intelligence & Question Extraction</h1>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.2rem;">Pragati Bharati Round 2 — Production-Oriented Review Service</p>
            </div>
            <div class="links">
                <a href="/docs" target="_blank">Swagger API Docs</a>
                <a href="/redoc" target="_blank">ReDoc</a>
                <a href="/health" target="_blank">Health Check</a>
            </div>
        </header>

        <div class="grid">
            <div>
                <div class="card">
                    <div class="card-title">1. Authentication (JWT)</div>
                    <div class="form-group">
                        <label>Email</label>
                        <input id="auth_email" value="reviewer@example.com">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input id="auth_password" type="password" value="reviewerpassword123">
                    </div>
                    <button onclick="authenticate()">Register / Login</button>
                    <span id="auth_status" style="margin-left: 1rem; font-size: 0.85rem; color: var(--text-muted);">Not authenticated</span>
                </div>

                <div class="card">
                    <div class="card-title">2. Upload Document</div>
                    <div class="form-group">
                        <label>Select PDF or Image</label>
                        <input id="upload_file" type="file" accept=".pdf,.png,.jpg,.jpeg">
                    </div>
                    <div class="form-group">
                        <label>Document Type</label>
                        <select id="upload_type">
                            <option value="QUESTION_PAPER">Question Paper</option>
                            <option value="ANSWER_KEY">Answer Key</option>
                            <option value="UNSPECIFIED">Unspecified</option>
                        </select>
                    </div>
                    <button onclick="uploadDoc()">Upload & Process</button>
                    <div id="upload_result" style="margin-top: 1rem;"></div>
                </div>
            </div>

            <div>
                <div class="card">
                    <div class="card-title">3. Processing Status</div>
                    <div id="status_display" style="color: var(--text-muted); font-size: 0.9rem;">No active document selected.</div>
                </div>

                <div class="card">
                    <div class="card-title">4. Extracted Questions & Review</div>
                    <div id="questions_container" style="max-height: 500px; overflow-y: auto;">
                        <p style="color: var(--text-muted); font-size: 0.85rem;">Upload a document to view extracted questions and confidence ratings.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let token = localStorage.getItem("doc_token") || "";
        let currentDocId = "";

        if (token) {
            document.getElementById("auth_status").innerText = "Token loaded from session";
            document.getElementById("auth_status").style.color = "var(--success)";
        }

        async function authenticate() {
            const email = document.getElementById("auth_email").value;
            const password = document.getElementById("auth_password").value;

            // Try register first, then login
            try {
                await fetch("/api/v1/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
            } catch (e) {}

            const res = await fetch("/api/v1/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            if (res.ok) {
                const data = await res.json();
                token = data.access_token;
                localStorage.setItem("doc_token", token);
                document.getElementById("auth_status").innerText = "Authenticated";
                document.getElementById("auth_status").style.color = "var(--success)";
            } else {
                document.getElementById("auth_status").innerText = "Authentication failed";
                document.getElementById("auth_status").style.color = "var(--danger)";
            }
        }

        async function uploadDoc() {
            if (!token) {
                alert("Please authenticate first!");
                return;
            }
            const fileInput = document.getElementById("upload_file");
            if (!fileInput.files[0]) {
                alert("Please select a file to upload.");
                return;
            }

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            formData.append("document_type", document.getElementById("upload_type").value);

            const res = await fetch("/api/v1/documents/upload", {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                currentDocId = data.document_id;
                document.getElementById("upload_result").innerHTML = `
                    <div style="font-size: 0.85rem; color: var(--success)">
                        Accepted: <b>${data.original_filename}</b> (ID: ${data.document_id})
                    </div>
                `;
                pollStatus();
            } else {
                const err = await res.json();
                alert("Upload error: " + JSON.stringify(err));
            }
        }

        async function pollStatus() {
            if (!currentDocId) return;
            const res = await fetch(`/api/v1/documents/${currentDocId}/status`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById("status_display").innerHTML = `
                    <div><b>Status:</b> ${data.status}</div>
                    <div style="margin: 0.5rem 0;"><b>Progress:</b> ${data.progress_pct}%</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">${data.current_step}</div>
                `;
                if (data.status === "COMPLETED" || data.status === "FAILED") {
                    loadQuestions();
                } else {
                    setTimeout(pollStatus, 1500);
                }
            }
        }

        async function loadQuestions() {
            if (!currentDocId) return;
            const res = await fetch(`/api/v1/documents/${currentDocId}/questions`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const warnRes = await fetch(`/api/v1/documents/${currentDocId}/warnings`, {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                const warnings = warnRes.ok ? await warnRes.json() : [];
                const container = document.getElementById("questions_container");
                container.innerHTML = `
                    <div style="margin-bottom: 0.8rem; font-size: 0.85rem;">
                        <b>Total:</b> ${data.total_count} | 
                        <span style="color: var(--success)">Extracted: ${data.extracted_count}</span> | 
                        <span style="color: var(--warning)">Review: ${data.review_required_count}</span>
                    </div>
                `;

                data.questions.forEach(q => {
                    const badgeClass = q.confidence_score >= 0.8 ? 'badge-success' : (q.confidence_score >= 0.5 ? 'badge-warning' : 'badge-danger');
                    const qWarnings = warnings.filter(w => w.question_id === q.id);
                    
                    let optionsHtml = "";
                    if (q.options && q.options.length) {
                        optionsHtml = q.options.map(opt => `
                            <div class="option-item ${q.detected_answer === opt.key ? 'option-correct' : ''}">
                                <b>(${opt.key})</b> ${opt.text} ${q.detected_answer === opt.key ? '✓ [Detected Answer]' : ''}
                            </div>
                        `).join("");
                    }

                    let warningsHtml = "";
                    if (qWarnings.length) {
                        warningsHtml = qWarnings.map(w => `
                            <div class="warning-box">⚠ [${w.warning_code}]: ${w.message}</div>
                        `).join("");
                    }

                    container.innerHTML += `
                        <div class="question-box">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <b>${q.question_number ? 'Q' + q.question_number : '<Unnumbered Question>'}</b>
                                <div>
                                    <span class="badge ${badgeClass}">${(q.confidence_score * 100).toFixed(0)}% Conf</span>
                                    <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: 0.5rem;">Pages: [${q.source_pages.join(', ')}]</span>
                                </div>
                            </div>
                            <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">${q.question_text}</div>
                            ${optionsHtml}
                            ${warningsHtml}
                        </div>
                    `;
                });
            }
        }
    </script>
</body>
</html>
    """
