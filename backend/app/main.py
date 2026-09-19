from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

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
    title="DocuQ — Document Intelligence & Question Extraction Service",
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

# Serve React Production Build
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "message": "DocuQ API is operational. Start the frontend via .\\run_frontend.ps1 or run 'npm run build' in frontend/.",
            "docs": "/docs",
            "health": "/health",
        }
