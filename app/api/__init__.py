from fastapi import APIRouter

from . import analytics, receipts

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(receipts.router, prefix="/receipts", tags=["receipts"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
