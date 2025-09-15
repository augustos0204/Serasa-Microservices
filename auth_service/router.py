from fastapi import APIRouter
from routes import health
from routes import user
from routes import auth

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(user.router)
router.include_router(auth.router)