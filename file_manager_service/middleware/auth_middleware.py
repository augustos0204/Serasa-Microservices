import os
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header required"}
            )

        token = auth_header.split(" ")[1]

        auth_service_url = os.getenv("AUTH_SERVICE_URL")
        if not auth_service_url:
            return JSONResponse(
                status_code=500,
                content={"detail": "Auth service configuration missing"}
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{auth_service_url}/auth/validate",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0
                )

            if response.status_code != 200:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"}
                )

            return await call_next(request)

        except Exception:
            return JSONResponse(
                status_code=500,
                content={"detail": "Authentication service unavailable"}
            )