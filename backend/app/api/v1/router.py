from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.documents import router as documents_router
from app.api.v1.questions import router as questions_router
from app.api.v1.warnings import router as warnings_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(questions_router)
api_v1_router.include_router(warnings_router)


@api_v1_router.get("/health", tags=["Health"])
async def api_v1_health():
    return {"status": "healthy", "version": "v1"}
