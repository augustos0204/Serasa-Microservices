from fastapi import APIRouter
from routes import health, process, file_inconsistencies

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(process.router, tags=["process"])
router.include_router(file_inconsistencies.router, tags=["file-inconsistencies"])