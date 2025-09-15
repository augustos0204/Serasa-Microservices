from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dependencies.auth_deps import get_current_user
from models.database import AsyncSessionLocal


class AuthMiddleware(BaseHTTPMiddleware):

    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/auth/login",
    }

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)


        return await call_next(request)