from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.settings import settings

app = FastAPI(
    title="Receipt OCR & Analytics Platform",
    version="1.0.0",
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(api_router)
