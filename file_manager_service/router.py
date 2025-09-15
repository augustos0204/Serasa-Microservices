from fastapi import APIRouter
from routes import health, files

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(files.router, tags=["files"])