from fastapi import APIRouter, Depends

from app.api.routes import auth, documents, jobs, profile
from app.core.deps import get_current_user

api_router = APIRouter(prefix="/api/v1")

# Public
api_router.include_router(auth.router)

# Protected — all routes below require a valid access token
_protected = {"dependencies": [Depends(get_current_user)]}
api_router.include_router(jobs.router, **_protected)
api_router.include_router(profile.router, **_protected)
api_router.include_router(documents.router, **_protected)
