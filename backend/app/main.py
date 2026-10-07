from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.brands import router as brands_router
from app.api.detections import router as detections_router
from app.api.monitoring import router as monitoring_router
from app.api.dashboard import router as dashboard_router
from app.api.investigations import router as investigations_router
from app.core.config import get_settings
from app.logos import ensure_logo_directory

settings = get_settings()
app = FastAPI(title="BrandShield API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")
app.include_router(brands_router, prefix="/api")
app.include_router(detections_router, prefix="/api")
app.include_router(investigations_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.mount("/static/logos", StaticFiles(directory=ensure_logo_directory()), name="logos")
