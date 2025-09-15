from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
from typing import Optional

security = HTTPBearer()

async def validate_token_with_auth_service(token: str) -> bool:
    auth_service_url = os.getenv("AUTH_SERVICE_URL")
    if not auth_service_url:
        raise ValueError("AUTH_SERVICE_URL environment variable not set")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{auth_service_url}/auth/validate",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            return response.status_code == 200

    except Exception:
        return False

async def require_authentication(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if not await validate_token_with_auth_service(credentials.credentials):
        raise credentials_exception

    return credentials.credentials