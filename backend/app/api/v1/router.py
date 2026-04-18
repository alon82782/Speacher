from fastapi import APIRouter
from app.api.v1 import auth, analysis

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
