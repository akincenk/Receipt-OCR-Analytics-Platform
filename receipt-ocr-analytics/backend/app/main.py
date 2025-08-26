from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router

app = FastAPI(
    title="Receipt OCR & Analytics Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(api_router)
