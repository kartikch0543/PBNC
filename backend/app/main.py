from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import init_database
from app.core.errors import AppError
import app.models  # Register all models for metadata

logger = logging.getLogger("document_intelligence")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Automatically initializes database tables on startup (with fallback support)."""
    await init_database()
    yield


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
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Inline SVG favicon to eliminate 404 noise in browser requests."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#38bdf8"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>"""
    return Response(content=svg, media_type="image/svg+xml")


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


# Professional Review & Intelligence Dashboard
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_review_dashboard():
    """Serves the executive-grade Document Intelligence & Human Review Dashboard."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Intelligence & Question Extraction Service</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --surface: #111827;
            --surface-elevated: #1a2234;
            --surface-border: #243049;
            --surface-border-hover: #3b82f6;
            --primary: #3b82f6;
            --primary-gradient: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
            --accent: #06b6d4;
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-tertiary: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --shadow-subtle: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
            --shadow-glow: 0 0 25px -5px rgba(59, 130, 246, 0.25);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif; }
        body { background: var(--bg); color: var(--text-main); line-height: 1.5; min-height: 100vh; display: flex; flex-direction: column; }
        code, pre { font-family: 'JetBrains Mono', monospace; }

        /* Navigation Header */
        header {
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--surface-border);
            padding: 0.85rem 2rem;
            position: sticky;
            top: 0;
            z-index: 50;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand { display: flex; align-items: center; gap: 0.85rem; }
        .brand-icon {
            width: 38px; height: 38px; border-radius: var(--radius-sm);
            background: var(--primary-gradient); display: flex; align-items: center; justify-content: center;
            box-shadow: var(--shadow-glow); flex-shrink: 0;
        }
        .brand-icon svg { width: 20px; height: 20px; fill: #fff; }
        .brand-name { font-size: 1.05rem; font-weight: 800; letter-spacing: -0.02em; color: #fff; }
        .brand-tag { font-size: 0.7rem; font-weight: 600; color: var(--accent); text-transform: uppercase; letter-spacing: 0.08em; }

        .header-actions { display: flex; align-items: center; gap: 1.25rem; }
        .system-pill {
            display: flex; align-items: center; gap: 0.5rem; background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 9999px; padding: 0.25rem 0.75rem;
            font-size: 0.78rem; font-weight: 600; color: var(--success);
        }
        .pulse-dot { width: 7px; height: 7px; background: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); }
        .nav-link { color: var(--text-secondary); text-decoration: none; font-size: 0.82rem; font-weight: 600; transition: color 0.2s; }
        .nav-link:hover { color: var(--text-main); }

        .header-user-badge {
            display: none; align-items: center; gap: 0.5rem; background: var(--surface-elevated);
            border: 1px solid var(--surface-border); border-radius: 9999px; padding: 0.25rem 0.75rem;
            font-size: 0.78rem; color: #cbd5e1;
        }
        .header-logout-btn {
            background: transparent; border: none; color: var(--danger); cursor: pointer;
            font-size: 0.75rem; font-weight: 700; text-decoration: underline; margin-left: 0.25rem;
        }

        /* Main Workspace Layout */
        .workspace { max-width: 1440px; margin: 0 auto; padding: 1.75rem 2rem; width: 100%; flex: 1; }
        .grid { display: grid; grid-template-columns: 400px 1fr; gap: 1.75rem; align-items: start; }

        /* Left Column: Sticky Sidebar */
        .left-sidebar {
            position: sticky;
            top: 5rem;
            max-height: calc(100vh - 6.5rem);
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            padding-right: 4px;
        }
        .left-sidebar::-webkit-scrollbar { width: 5px; }
        .left-sidebar::-webkit-scrollbar-thumb { background: var(--surface-border); border-radius: 9999px; }

        /* Cards */
        .card {
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            box-shadow: var(--shadow-subtle);
            position: relative;
        }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.1rem; }
        .card-title { font-size: 1rem; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 0.5rem; }
        .card-desc { font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem; }

        /* Auth Tabs & Form */
        .auth-switch { display: flex; background: var(--bg); border-radius: var(--radius-sm); padding: 3px; margin-bottom: 1.1rem; border: 1px solid var(--surface-border); }
        .auth-tab {
            flex: 1; padding: 0.4rem; text-align: center; font-size: 0.8rem; font-weight: 600; cursor: pointer;
            border-radius: 6px; color: var(--text-secondary); transition: all 0.2s;
        }
        .auth-tab.active { background: var(--surface-elevated); color: #fff; border: 1px solid var(--surface-border); }

        /* Logged In User Profile Card */
        .user-profile-view {
            display: none;
            background: rgba(16, 185, 129, 0.04);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: var(--radius-md);
            padding: 1.25rem;
            margin-top: 0.25rem;
        }
        .user-profile-header { display: flex; align-items: center; gap: 0.85rem; margin-bottom: 1rem; }
        .user-avatar {
            width: 44px; height: 44px; border-radius: 50%;
            background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem; font-weight: 800; color: #000; flex-shrink: 0;
        }
        .user-email-text { font-size: 0.92rem; font-weight: 700; color: #fff; word-break: break-all; }
        .user-role-badge {
            display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.72rem; font-weight: 700;
            color: #34d399; background: rgba(16, 185, 129, 0.15); padding: 0.2rem 0.55rem; border-radius: 9999px;
            margin-top: 0.25rem;
        }
        .user-meta-note {
            font-size: 0.78rem; color: var(--text-tertiary); line-height: 1.4;
            padding: 0.6rem 0.75rem; background: var(--bg); border-radius: var(--radius-sm);
            border: 1px solid var(--surface-border); margin-bottom: 1rem;
        }
        .btn-logout {
            width: 100%; padding: 0.65rem; background: transparent; border: 1px solid rgba(239, 68, 68, 0.4);
            color: #f87171; border-radius: var(--radius-sm); font-size: 0.82rem; font-weight: 600;
            cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 0.5rem;
        }
        .btn-logout:hover { background: rgba(239, 68, 68, 0.1); border-color: var(--danger); color: #fca5a5; }

        /* Forms & Inputs */
        .form-group { margin-bottom: 1rem; }
        .form-label { display: block; font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.35rem; }
        .form-input {
            width: 100%; padding: 0.7rem 0.9rem; background: var(--bg); border: 1px solid var(--surface-border);
            border-radius: var(--radius-sm); color: #fff; font-size: 0.85rem; transition: all 0.2s;
        }
        .form-input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15); }

        /* Buttons */
        .btn {
            display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
            font-weight: 600; font-size: 0.85rem; border-radius: var(--radius-sm); padding: 0.7rem 1.15rem;
            cursor: pointer; transition: all 0.2s; border: none; width: 100%;
        }
        .btn-primary { background: var(--primary-gradient); color: #fff; box-shadow: var(--shadow-glow); }
        .btn-primary:hover { opacity: 0.95; transform: translateY(-1px); }
        .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .btn-outline { background: transparent; border: 1px solid var(--surface-border); color: var(--text-secondary); }
        .btn-outline:hover { border-color: var(--primary); color: #fff; }

        /* Drag & Drop File Upload Area */
        .dropzone {
            border: 2px dashed var(--surface-border);
            border-radius: var(--radius-md);
            padding: 1.5rem 1rem;
            text-align: center;
            background: rgba(9, 13, 22, 0.5);
            cursor: pointer;
            transition: all 0.25s;
            position: relative;
        }
        .dropzone:hover, .dropzone.dragover { border-color: var(--primary); background: rgba(59, 130, 246, 0.05); }
        .dropzone-icon { width: 38px; height: 38px; margin: 0 auto 0.5rem; fill: var(--primary); }
        .dropzone-title { font-size: 0.9rem; font-weight: 700; color: #fff; }
        .dropzone-sub { font-size: 0.75rem; color: var(--text-tertiary); margin-top: 0.25rem; }
        .file-input { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; }

        /* Active file display */
        .selected-file-banner {
            display: none; align-items: center; justify-content: space-between;
            padding: 0.6rem 0.85rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: var(--radius-sm); margin-top: 0.85rem; font-size: 0.8rem; color: var(--accent);
        }

        /* Sample Quick Load Buttons */
        .sample-loader-box { margin-top: 1.15rem; padding-top: 1.15rem; border-top: 1px solid var(--surface-border); }
        .sample-loader-box p { font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
        .sample-btn-group { display: flex; flex-wrap: wrap; gap: 0.45rem; }
        .btn-chip {
            background: var(--surface-elevated); border: 1px solid var(--surface-border); color: var(--text-secondary);
            font-size: 0.74rem; font-weight: 600; padding: 0.35rem 0.65rem; border-radius: 6px; cursor: pointer; transition: all 0.15s;
        }
        .btn-chip:hover { border-color: var(--primary); color: #fff; }

        /* Execution Progress Tracker */
        .timeline-box { margin-bottom: 1.25rem; }
        .progress-bar-bg { width: 100%; height: 6px; background: var(--bg); border-radius: 9999px; overflow: hidden; margin-top: 0.65rem; }
        .progress-bar-fill { height: 100%; background: var(--primary-gradient); width: 0%; transition: width 0.3s ease; }
        .status-msg { font-size: 0.8rem; color: var(--accent); margin-top: 0.45rem; font-weight: 500; }

        /* Results & Inspection Section */
        .metrics-banner {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.85rem; margin-bottom: 1.25rem;
        }
        .metric-card {
            background: var(--surface-elevated); border: 1px solid var(--surface-border); border-radius: var(--radius-md);
            padding: 0.85rem; text-align: center;
        }
        .metric-val { font-size: 1.35rem; font-weight: 800; color: #fff; }
        .metric-lbl { font-size: 0.68rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-top: 0.15rem; }

        /* Toolbar / Filter Row */
        .explorer-toolbar {
            display: flex; justify-content: space-between; align-items: center; gap: 0.85rem;
            margin-bottom: 1.15rem; flex-wrap: wrap;
        }
        .search-input-box {
            flex: 1; min-width: 220px; position: relative;
        }
        .search-input-box input {
            width: 100%; padding: 0.55rem 0.85rem 0.55rem 2.2rem; background: var(--surface-elevated);
            border: 1px solid var(--surface-border); border-radius: var(--radius-sm); color: #fff; font-size: 0.82rem;
        }
        .search-input-box svg {
            position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); width: 14px; height: 14px; fill: var(--text-tertiary);
        }
        .filter-group { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }
        .filter-btn {
            background: var(--surface-elevated); border: 1px solid var(--surface-border); border-radius: 6px;
            color: var(--text-secondary); font-size: 0.75rem; font-weight: 600; padding: 0.45rem 0.75rem;
            cursor: pointer; transition: all 0.2s;
        }
        .filter-btn.active { background: rgba(59, 130, 246, 0.15); border-color: var(--primary); color: #93c5fd; }
        .btn-json-inspect {
            background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 6px;
            color: #67e8f9; font-size: 0.75rem; font-weight: 700; padding: 0.45rem 0.75rem; cursor: pointer;
            display: inline-flex; align-items: center; gap: 0.35rem; transition: all 0.2s;
        }
        .btn-json-inspect:hover { background: rgba(6, 182, 212, 0.2); }

        /* Question Cards */
        .question-item {
            background: var(--surface-elevated); border: 1px solid var(--surface-border); border-radius: var(--radius-md);
            padding: 1.25rem; margin-bottom: 0.95rem; transition: border-color 0.2s;
        }
        .question-item:hover { border-color: var(--surface-border-hover); }
        .q-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem; }
        .q-badge {
            font-size: 0.8rem; font-weight: 700; padding: 0.25rem 0.55rem; border-radius: 6px;
            background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .q-pages { font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; color: var(--text-tertiary); }
        
        .confidence-pill {
            font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 9999px;
            display: inline-flex; align-items: center; gap: 0.35rem;
        }
        .conf-high { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .conf-warn { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .conf-danger { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }

        .q-stem { font-size: 0.92rem; font-weight: 600; color: #f1f5f9; margin-bottom: 0.85rem; line-height: 1.55; }

        /* Options list */
        .option-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.55rem; margin-bottom: 0.65rem; }
        .opt-item {
            padding: 0.55rem 0.75rem; border-radius: var(--radius-sm); background: var(--bg);
            border: 1px solid var(--surface-border); font-size: 0.82rem; color: var(--text-secondary);
            display: flex; align-items: center; gap: 0.55rem;
        }
        .opt-item.matched {
            border-color: rgba(16, 185, 129, 0.5); background: rgba(16, 185, 129, 0.08); color: #a7f3d0; font-weight: 600;
        }
        .opt-key {
            font-weight: 700; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;
            border-radius: 4px; background: var(--surface-border); color: #fff; font-size: 0.72rem; flex-shrink: 0;
        }
        .opt-item.matched .opt-key { background: var(--success); color: #000; }

        /* Warnings & Audits */
        .warn-flag {
            background: rgba(245, 158, 11, 0.08); border-left: 3px solid var(--warning); padding: 0.5rem 0.75rem;
            border-radius: 0 6px 6px 0; font-size: 0.75rem; color: #fde68a; margin-top: 0.5rem;
        }

        /* Empty / Placeholder State */
        .empty-state { text-align: center; padding: 3.5rem 1.5rem; color: var(--text-tertiary); }
        .empty-icon { width: 48px; height: 48px; margin: 0 auto 0.85rem; fill: var(--surface-border); }

        /* Notification Toast */
        #toast {
            position: fixed; bottom: 2rem; right: 2rem; background: var(--surface-elevated); border: 1px solid var(--surface-border);
            padding: 0.75rem 1.25rem; border-radius: var(--radius-md); box-shadow: var(--shadow-subtle); display: none;
            font-size: 0.82rem; font-weight: 600; z-index: 100; max-width: 380px;
        }

        /* Structured Output Modal */
        .modal-overlay {
            display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px); z-index: 200; align-items: center; justify-content: center; padding: 1.5rem;
        }
        .modal-card {
            background: var(--surface); border: 1px solid var(--surface-border); border-radius: var(--radius-lg);
            width: 100%; max-width: 800px; max-height: 85vh; display: flex; flex-direction: column;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8);
        }
        .modal-header {
            padding: 1.15rem 1.5rem; border-bottom: 1px solid var(--surface-border);
            display: flex; justify-content: space-between; align-items: center;
        }
        .modal-title { font-size: 1rem; font-weight: 700; color: #fff; }
        .modal-body {
            padding: 1.25rem 1.5rem; overflow-y: auto; flex: 1; background: #070a10;
        }
        .modal-code {
            font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #a5f3fc;
            white-space: pre-wrap; word-break: break-all;
        }
        .modal-footer {
            padding: 1rem 1.5rem; border-top: 1px solid var(--surface-border);
            display: flex; justify-content: flex-end; gap: 0.75rem;
        }

        /* Responsive Breakpoints */
        @media (max-width: 1024px) {
            .workspace { padding: 1.25rem 1rem; }
            .grid { grid-template-columns: 1fr; gap: 1.5rem; }
            .left-sidebar { position: static; max-height: none; overflow-y: visible; padding-right: 0; }
            .metrics-banner { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 640px) {
            header { padding: 0.75rem 1rem; flex-direction: column; align-items: stretch; gap: 0.75rem; }
            .header-actions { justify-content: space-between; flex-wrap: wrap; }
            .metrics-banner { grid-template-columns: 1fr; }
            .option-grid { grid-template-columns: 1fr; }
            .explorer-toolbar { flex-direction: column; align-items: stretch; }
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="brand-icon">
                <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
            </div>
            <div>
                <div class="brand-name">Document Intelligence & Question Extraction Service</div>
            </div>
        </div>
        <div class="header-actions">
            <div class="system-pill">
                <div class="pulse-dot"></div>
                <span>Service Operational</span>
            </div>
            <div id="headerUserBadge" class="header-user-badge">
                <span id="headerUserEmail">user@example.com</span>
                <button type="button" class="header-logout-btn" onclick="handleLogout()">Sign Out</button>
            </div>
            <a href="/docs" target="_blank" class="nav-link">Swagger UI</a>
            <a href="/redoc" target="_blank" class="nav-link">ReDoc</a>
            <a href="https://github.com/kartikch0543/PBNC" target="_blank" class="nav-link">GitHub</a>
        </div>
    </header>

    <main class="workspace">
        <div class="grid">
            <!-- Left Column: Sticky Control Panel -->
            <div class="left-sidebar">
                <!-- Authentication Card -->
                <div class="card" id="authCard">
                    <div class="card-header">
                        <div>
                            <div class="card-title">User Authentication</div>
                            <div class="card-desc" id="authDesc">OAuth2 Bearer JWT authorization</div>
                        </div>
                        <span id="authBadge" style="font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary);">GUEST</span>
                    </div>

                    <!-- Logged Out View: Tab Switch + Inputs -->
                    <div id="loggedOutView">
                        <div class="auth-switch" id="authSwitch">
                            <div id="tabLogin" class="auth-tab active" onclick="setAuthMode('login')">Log In</div>
                            <div id="tabRegister" class="auth-tab" onclick="setAuthMode('register')">Create Account</div>
                        </div>

                        <form id="authForm" onsubmit="handleAuth(event)">
                            <div class="form-group">
                                <label class="form-label">Email Address</label>
                                <input id="authEmail" type="email" class="form-input" placeholder="e.g. evaluator@pragatibharati.org" required autocomplete="email">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Password</label>
                                <input id="authPassword" type="password" class="form-input" placeholder="Minimum 8 characters" minlength="8" required autocomplete="current-password">
                            </div>
                            <button type="submit" id="authSubmitBtn" class="btn btn-primary">Log In</button>
                        </form>
                    </div>

                    <!-- Logged In View: Profile Details + Log Out -->
                    <div id="loggedInView" class="user-profile-view">
                        <div class="user-profile-header">
                            <div id="userAvatar" class="user-avatar">U</div>
                            <div style="min-width: 0;">
                                <div id="userProfileEmail" class="user-email-text">user@example.com</div>
                                <div class="user-role-badge">
                                    <span>● Active Session</span>
                                </div>
                            </div>
                        </div>
                        <div class="user-meta-note">
                            OAuth2 Bearer token is active. Your session token is automatically attached to document ingestion and question extraction requests.
                        </div>
                        <button type="button" class="btn-logout" onclick="handleLogout()">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M16 13v-2H7V8l-5 4 5 4v-3zM20 3H10c-1.1 0-2 .9-2 2v4h2V5h10v14H10v-4H8v4c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>
                            Log Out
                        </button>
                    </div>
                </div>

                <!-- Ingestion & Upload Card -->
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Document Ingestion</div>
                            <div class="card-desc">Accepts digital PDFs, scans, and images</div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Document Role</label>
                        <select id="docTypeSelect" class="form-input">
                            <option value="QUESTION_PAPER">Question Paper</option>
                            <option value="ANSWER_KEY">Standalone Answer Key</option>
                            <option value="UNSPECIFIED">Unspecified Document</option>
                        </select>
                    </div>

                    <div class="dropzone" id="dropArea">
                        <svg class="dropzone-icon" viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
                        <div class="dropzone-title">Click or drag examination document here</div>
                        <div class="dropzone-sub">Supported formats: PDF, PNG, JPG (Max 25MB)</div>
                        <input type="file" id="fileInput" class="file-input" accept=".pdf,.png,.jpg,.jpeg">
                    </div>

                    <div id="fileBanner" class="selected-file-banner">
                        <span id="fileBannerName" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 260px;">document.pdf</span>
                        <span style="font-size: 0.75rem; cursor: pointer; color: var(--danger); font-weight: 600;" onclick="clearSelectedFile()">Remove</span>
                    </div>

                    <button type="button" id="uploadBtn" class="btn btn-primary" style="margin-top: 1.15rem;" onclick="uploadDocument()">
                        Upload & Begin Asynchronous Extraction
                    </button>

                    <!-- Pre-generated Sample Test Set Quick Buttons -->
                    <div class="sample-loader-box">
                        <p>Evaluate With Curated Samples</p>
                        <div class="sample-btn-group">
                            <button type="button" class="btn-chip" onclick="loadSampleDoc('sample_01_clean.pdf', 'QUESTION_PAPER')">Clean PDF (4 Qs)</button>
                            <button type="button" class="btn-chip" onclick="loadSampleDoc('sample_04_multi_page_question.pdf', 'QUESTION_PAPER')">Multi-Page Q2</button>
                            <button type="button" class="btn-chip" onclick="loadSampleDoc('sample_03_low_quality.png', 'QUESTION_PAPER')">Scan Image (PNG)</button>
                            <button type="button" class="btn-chip" onclick="loadSampleDoc('sample_05_question_paper.pdf', 'QUESTION_PAPER')">Unanswered Paper</button>
                            <button type="button" class="btn-chip" onclick="loadSampleDoc('sample_06_separate_answer_key.pdf', 'ANSWER_KEY')">Separate Answer Key</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column: Live Pipeline Monitor & Question Explorer -->
            <div>
                <!-- Async Execution Pipeline Tracker -->
                <div class="card" style="margin-bottom: 1.25rem;">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Processing Pipeline Status</div>
                            <div id="pipelineSub" class="card-desc">Awaiting document submission</div>
                        </div>
                        <span id="statusBadge" class="confidence-pill" style="display: none;">QUEUED</span>
                    </div>

                    <div class="timeline-box">
                        <div style="display: flex; justify-content: space-between; font-size: 0.82rem; font-weight: 600;">
                            <span id="currentStepText">Idle</span>
                            <span id="progressPctText">0%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div id="progressBarFill" class="progress-bar-fill"></div>
                        </div>
                        <div id="statusMessage" class="status-msg"></div>
                    </div>
                </div>

                <!-- Extracted Questions & Review Section -->
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Extracted Questions & Audit Flags</div>
                            <div class="card-desc">Machine-readable question stems, options, and confidence validation</div>
                        </div>
                    </div>

                    <!-- Metric Counters -->
                    <div id="metricsRow" class="metrics-banner" style="display: none;">
                        <div class="metric-card">
                            <div id="metricTotal" class="metric-val">0</div>
                            <div class="metric-lbl">Total Questions</div>
                        </div>
                        <div class="metric-card">
                            <div id="metricExtracted" class="metric-val" style="color: var(--success);">0</div>
                            <div class="metric-lbl">Extracted</div>
                        </div>
                        <div class="metric-card">
                            <div id="metricReview" class="metric-val" style="color: var(--warning);">0</div>
                            <div class="metric-lbl">Review Items</div>
                        </div>
                        <div class="metric-card">
                            <div id="metricAnswered" class="metric-val" style="color: var(--accent);">0</div>
                            <div class="metric-lbl">Answers Matched</div>
                        </div>
                    </div>

                    <!-- Interactive Explorer Toolbar -->
                    <div id="explorerToolbar" class="explorer-toolbar" style="display: none;">
                        <div class="search-input-box">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                            <input type="text" id="questionSearchInput" placeholder="Filter questions by keywords..." oninput="handleQuestionFilter()">
                        </div>
                        <div class="filter-group">
                            <button type="button" class="filter-btn active" id="filterAll" onclick="setFilterMode('ALL')">All</button>
                            <button type="button" class="filter-btn" id="filterHigh" onclick="setFilterMode('HIGH')">High Conf (≥80%)</button>
                            <button type="button" class="filter-btn" id="filterReview" onclick="setFilterMode('REVIEW')">Review Required</button>
                            <button type="button" class="filter-btn" id="filterAnswered" onclick="setFilterMode('ANSWERED')">With Answer</button>
                            <button type="button" class="btn-json-inspect" onclick="openStructuredJsonModal()">
                                <span>{ }</span>
                                <span>Structured JSON</span>
                            </button>
                        </div>
                    </div>

                    <!-- Container for Question Cards -->
                    <div id="questionsList">
                        <div class="empty-state">
                            <svg class="empty-icon" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                            <div style="font-weight: 700; font-size: 0.95rem; color: #fff;">No questions currently displayed</div>
                            <p style="font-size: 0.82rem; margin-top: 0.35rem;">Log in or create an account, select an examination document, and initiate extraction to inspect results.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Structured Output JSON Modal -->
    <div id="jsonModal" class="modal-overlay" onclick="closeJsonModal(event)">
        <div class="modal-card" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div>
                    <div class="modal-title">Structured Output (Assignment Section 7 Schema)</div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px;">System-independent machine readable JSON</div>
                </div>
                <button type="button" style="background:none; border:none; color:var(--text-secondary); font-size:1.2rem; cursor:pointer;" onclick="closeJsonModal()">&times;</button>
            </div>
            <div class="modal-body">
                <pre id="jsonModalContent" class="modal-code">// No data</pre>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-outline" style="width:auto;" onclick="copyJsonToClipboard()">Copy JSON</button>
                <button type="button" class="btn btn-primary" style="width:auto;" onclick="closeJsonModal()">Close</button>
            </div>
        </div>
    </div>

    <div id="toast">Notification</div>

    <script>
        let authToken = localStorage.getItem("auth_token") || "";
        let currentUser = null;
        let authMode = "login";
        let activeDocId = null;
        let pollingInterval = null;
        let rawExtractedQuestions = [];
        let rawWarnings = [];
        let rawAnswers = [];
        let activeFilter = "ALL";

        // Initialization
        window.addEventListener("DOMContentLoaded", async () => {
            setupFileHandlers();
            if (authToken) {
                await verifyAndLoadUserSession();
            } else {
                renderAuthLoggedOut();
            }
        });

        function showToast(msg, isError = false) {
            const t = document.getElementById("toast");
            t.innerText = msg;
            t.style.color = isError ? "var(--danger)" : "var(--success)";
            t.style.borderColor = isError ? "rgba(239,68,68,0.4)" : "rgba(16,185,129,0.4)";
            t.style.display = "block";
            setTimeout(() => { t.style.display = "none"; }, 3500);
        }

        // ==========================================
        // AUTHENTICATION LOGIC & STATE HANDLING
        // ==========================================

        async function verifyAndLoadUserSession() {
            try {
                const res = await fetch("/api/v1/auth/me", {
                    headers: { "Authorization": `Bearer ${authToken}` }
                });

                if (res.ok) {
                    currentUser = await res.json();
                    renderAuthLoggedIn(currentUser);
                } else {
                    // Token invalid or expired
                    localStorage.removeItem("auth_token");
                    authToken = "";
                    currentUser = null;
                    renderAuthLoggedOut();
                }
            } catch (err) {
                renderAuthLoggedOut();
            }
        }

        function renderAuthLoggedIn(user) {
            document.getElementById("loggedOutView").style.display = "none";
            document.getElementById("loggedInView").style.display = "block";
            document.getElementById("authBadge").innerText = "AUTHENTICATED";
            document.getElementById("authBadge").style.color = "var(--success)";
            document.getElementById("authDesc").innerText = "Logged in as verified reviewer";

            document.getElementById("userProfileEmail").innerText = user.email || "user@example.com";
            const initial = (user.email ? user.email.charAt(0) : "U").toUpperCase();
            document.getElementById("userAvatar").innerText = initial;

            // Header sync
            const headerBadge = document.getElementById("headerUserBadge");
            headerBadge.style.display = "inline-flex";
            document.getElementById("headerUserEmail").innerText = user.email || "Authenticated";
        }

        function renderAuthLoggedOut() {
            document.getElementById("loggedOutView").style.display = "block";
            document.getElementById("loggedInView").style.display = "none";
            document.getElementById("authBadge").innerText = "GUEST";
            document.getElementById("authBadge").style.color = "var(--text-tertiary)";
            document.getElementById("authDesc").innerText = "OAuth2 Bearer JWT authorization";

            // Header sync
            document.getElementById("headerUserBadge").style.display = "none";
        }

        function handleLogout() {
            localStorage.removeItem("auth_token");
            authToken = "";
            currentUser = null;
            renderAuthLoggedOut();
            showToast("Logged out successfully");
        }

        function setAuthMode(mode) {
            authMode = mode;
            document.getElementById("tabLogin").classList.toggle("active", mode === "login");
            document.getElementById("tabRegister").classList.toggle("active", mode === "register");
            document.getElementById("authSubmitBtn").innerText = mode === "login" ? "Log In" : "Create Account";
        }

        async function handleAuth(e) {
            e.preventDefault();
            const email = document.getElementById("authEmail").value.trim();
            const password = document.getElementById("authPassword").value;

            const endpoint = authMode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/register";

            try {
                const res = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                const data = await res.json();

                if (!res.ok) {
                    showToast(data.detail || (data.error && data.error.message) || "Authentication failed", true);
                    return;
                }

                if (authMode === "register") {
                    showToast("Account created! Authenticating...");
                    // Immediate login upon registration
                    const loginRes = await fetch("/api/v1/auth/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email, password })
                    });
                    const loginData = await loginRes.json();
                    authToken = loginData.access_token;
                } else {
                    authToken = data.access_token;
                }

                localStorage.setItem("auth_token", authToken);
                document.getElementById("authEmail").value = "";
                document.getElementById("authPassword").value = "";

                await verifyAndLoadUserSession();
                showToast("Welcome! Session authenticated");
            } catch (err) {
                showToast("Network error connecting to API", true);
            }
        }

        // ==========================================
        // FILE HANDLING & DRAG-AND-DROP
        // ==========================================

        function setupFileHandlers() {
            const fileInput = document.getElementById("fileInput");
            const dropArea = document.getElementById("dropArea");

            fileInput.addEventListener("change", (e) => {
                if (e.target.files.length > 0) {
                    displaySelectedFile(e.target.files[0].name);
                }
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                dropArea.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropArea.classList.add('dragover');
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropArea.classList.remove('dragover');
                }, false);
            });

            dropArea.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    displaySelectedFile(files[0].name);
                }
            });
        }

        function displaySelectedFile(filename) {
            document.getElementById("fileBannerName").innerText = filename;
            document.getElementById("fileBanner").style.display = "flex";
        }

        function clearSelectedFile() {
            document.getElementById("fileInput").value = "";
            document.getElementById("fileBanner").style.display = "none";
        }

        async function loadSampleDoc(sampleName, docType) {
            document.getElementById("docTypeSelect").value = docType;
            showToast(`Loading sample: ${sampleName}...`);
            try {
                const res = await fetch(`/api/v1/documents/samples/${sampleName}`);
                if (res.ok) {
                    const blob = await res.blob();
                    const file = new File([blob], sampleName, { type: blob.type || "application/pdf" });
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    document.getElementById("fileInput").files = dt.files;
                    displaySelectedFile(sampleName);
                    showToast(`Loaded ${sampleName} — Ready to Upload`);
                } else {
                    displaySelectedFile(sampleName);
                }
            } catch (e) {
                displaySelectedFile(sampleName);
            }
        }

        // ==========================================
        // DOCUMENT UPLOAD & LIVE PIPELINE POLLING
        // ==========================================

        async function uploadDocument() {
            if (!authToken) {
                showToast("Please log in or create an account first", true);
                return;
            }

            const fileInput = document.getElementById("fileInput");
            const docType = document.getElementById("docTypeSelect").value;
            const formData = new FormData();
            formData.append("document_type", docType);

            if (!fileInput.files || fileInput.files.length === 0) {
                showToast("Please select a file or click a sample button first", true);
                return;
            }

            formData.append("file", fileInput.files[0]);

            showToast("Uploading examination document...");
            document.getElementById("uploadBtn").disabled = true;

            try {
                const res = await fetch("/api/v1/documents/upload", {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${authToken}` },
                    body: formData
                });

                const data = await res.json();
                document.getElementById("uploadBtn").disabled = false;

                if (!res.ok) {
                    showToast(data.detail || (data.error && data.error.message) || "Upload rejected", true);
                    return;
                }

                activeDocId = data.document_id;
                showToast(`Accepted: ${data.original_filename}`);
                startStatusPolling(activeDocId);
            } catch (err) {
                document.getElementById("uploadBtn").disabled = false;
                showToast("Network error uploading file", true);
            }
        }

        function startStatusPolling(docId) {
            if (pollingInterval) clearInterval(pollingInterval);

            const badge = document.getElementById("statusBadge");
            badge.style.display = "inline-flex";
            badge.className = "confidence-pill conf-warn";
            badge.innerText = "PROCESSING";

            pollStatus(docId);
            pollingInterval = setInterval(() => pollStatus(docId), 1000);
        }

        async function pollStatus(docId) {
            try {
                const res = await fetch(`/api/v1/documents/${docId}/status`, {
                    headers: { "Authorization": `Bearer ${authToken}` }
                });

                if (!res.ok) return;

                const data = await res.json();
                document.getElementById("progressBarFill").style.width = `${data.progress_pct}%`;
                document.getElementById("progressPctText").innerText = `${data.progress_pct}%`;
                document.getElementById("currentStepText").innerText = data.status;
                document.getElementById("statusMessage").innerText = data.current_step;

                const badge = document.getElementById("statusBadge");
                badge.innerText = data.status;

                if (data.status === "COMPLETED" || data.status === "COMPLETED_WITH_WARNINGS") {
                    badge.className = "confidence-pill conf-high";
                    clearInterval(pollingInterval);
                    loadExtractedQuestions(docId);
                } else if (data.status === "FAILED") {
                    badge.className = "confidence-pill conf-danger";
                    clearInterval(pollingInterval);
                    showToast("Document extraction pipeline failed", true);
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }

        // ==========================================
        // QUESTION RENDERING, FILTERING & AUDITING
        // ==========================================

        async function loadExtractedQuestions(docId) {
            try {
                const [qRes, warnRes, ansRes] = await Promise.all([
                    fetch(`/api/v1/documents/${docId}/questions`, { headers: { "Authorization": `Bearer ${authToken}` } }),
                    fetch(`/api/v1/documents/${docId}/warnings`, { headers: { "Authorization": `Bearer ${authToken}` } }),
                    fetch(`/api/v1/documents/${docId}/answers`, { headers: { "Authorization": `Bearer ${authToken}` } })
                ]);

                if (!qRes.ok) return;

                const qData = await qRes.json();
                rawExtractedQuestions = qData.questions || [];
                rawWarnings = warnRes.ok ? await warnRes.json() : [];
                const ansData = ansRes.ok ? await ansRes.json() : { answers: [] };
                rawAnswers = ansData.answers || [];

                // Metrics Banner
                document.getElementById("metricsRow").style.display = "grid";
                document.getElementById("explorerToolbar").style.display = "flex";
                document.getElementById("metricTotal").innerText = qData.total_count;
                document.getElementById("metricExtracted").innerText = qData.extracted_count;
                document.getElementById("metricReview").innerText = qData.review_required_count;
                document.getElementById("metricAnswered").innerText = ansData.answered_questions || 0;

                renderFilteredQuestions();
            } catch (err) {
                console.error("Error loading questions:", err);
            }
        }

        function setFilterMode(mode) {
            activeFilter = mode;
            ['filterAll', 'filterHigh', 'filterReview', 'filterAnswered'].forEach(id => {
                document.getElementById(id).classList.remove("active");
            });

            if (mode === "ALL") document.getElementById("filterAll").classList.add("active");
            if (mode === "HIGH") document.getElementById("filterHigh").classList.add("active");
            if (mode === "REVIEW") document.getElementById("filterReview").classList.add("active");
            if (mode === "ANSWERED") document.getElementById("filterAnswered").classList.add("active");

            renderFilteredQuestions();
        }

        function handleQuestionFilter() {
            renderFilteredQuestions();
        }

        function renderFilteredQuestions() {
            const query = (document.getElementById("questionSearchInput")?.value || "").toLowerCase();
            const listContainer = document.getElementById("questionsList");

            let filtered = rawExtractedQuestions.filter(q => {
                const textMatch = q.question_text.toLowerCase().includes(query) ||
                    (q.options && q.options.some(o => o.text.toLowerCase().includes(query)));
                if (!textMatch) return false;

                const confPct = Math.round(q.confidence_score * 100);
                if (activeFilter === "HIGH") return confPct >= 80;
                if (activeFilter === "REVIEW") return confPct < 80 || rawWarnings.some(w => w.question_id === q.id);
                if (activeFilter === "ANSWERED") return !!q.detected_answer;
                return true;
            });

            if (filtered.length === 0) {
                listContainer.innerHTML = `
                    <div class="empty-state">
                        <div style="font-weight: 700; color: #fff;">No questions match filter</div>
                        <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.3rem;">Try clearing your search query or switching to 'All'.</p>
                    </div>
                `;
                return;
            }

            listContainer.innerHTML = filtered.map(q => {
                const qWarnings = rawWarnings.filter(w => w.question_id === q.id);
                const confPct = Math.round(q.confidence_score * 100);
                let confClass = "conf-high";
                if (confPct < 50) confClass = "conf-danger";
                else if (confPct < 80) confClass = "conf-warn";

                let optionsHtml = "";
                if (q.options && q.options.length > 0) {
                    optionsHtml = `
                        <div class="option-grid">
                            ${q.options.map(opt => {
                                const isMatch = (q.detected_answer && opt.key && q.detected_answer.toUpperCase() === opt.key.toUpperCase());
                                return `
                                    <div class="opt-item ${isMatch ? 'matched' : ''}">
                                        <span class="opt-key">${opt.key}</span>
                                        <span>${opt.text}</span>
                                        ${isMatch ? '<span style="margin-left:auto; font-size:0.75rem;">✓ Answer</span>' : ''}
                                    </div>
                                `;
                            }).join("")}
                        </div>
                    `;
                }

                const warningsHtml = qWarnings.map(w => `
                    <div class="warn-flag">⚠ [${w.warning_code}] ${w.message}</div>
                `).join("");

                return `
                    <div class="question-item">
                        <div class="q-header">
                            <span class="q-badge">${q.question_number ? 'Q' + q.question_number : 'Unnumbered Question'}</span>
                            <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
                                <span class="confidence-pill ${confClass}">${confPct}% Confidence</span>
                                <span class="q-pages">Page(s): ${q.source_pages.join(", ")}</span>
                            </div>
                        </div>
                        <div class="q-stem">${q.question_text}</div>
                        ${optionsHtml}
                        ${warningsHtml}
                    </div>
                `;
            }).join("");
        }

        // ==========================================
        // STRUCTURED OUTPUT MODAL (ASSIGNMENT SEC 7)
        // ==========================================

        function openStructuredJsonModal() {
            const structuredData = rawExtractedQuestions.map(q => ({
                question: q.question_text,
                options: (q.options || []).map(o => o.text),
                answer: q.detected_answer || null,
                source_pages: q.source_pages || [],
                confidence: Math.round(q.confidence_score * 100) / 100
            }));

            document.getElementById("jsonModalContent").innerText = JSON.stringify(structuredData, null, 2);
            document.getElementById("jsonModal").style.display = "flex";
        }

        function closeJsonModal(e) {
            if (!e || e.target.id === "jsonModal" || e.type === "click") {
                document.getElementById("jsonModal").style.display = "none";
            }
        }

        function copyJsonToClipboard() {
            const content = document.getElementById("jsonModalContent").innerText;
            navigator.clipboard.writeText(content).then(() => {
                showToast("Copied Structured JSON to clipboard!");
            }).catch(() => {
                showToast("Failed to copy to clipboard", true);
            });
        }
    </script>
</body>
</html>
    """
