from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.brands import router as brands_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title="BrandShield API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")
app.include_router(brands_router, prefix="/api")
