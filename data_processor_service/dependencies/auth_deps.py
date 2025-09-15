from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
from typing import Optional, Dict

security = HTTPBearer()

async def validate_token_with_auth_service(token: str) -> Optional[Dict]:
    """Validate JWT token by calling Auth Service /auth/validate endpoint"""
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

            if response.status_code == 200:
                return response.json()
            else:
                return None

    except Exception:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """Validate JWT token and return user info"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token_data = await validate_token_with_auth_service(credentials.credentials)
    if token_data is None:
        raise credentials_exception

    return token_data

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict]:
    """Get current user if authenticated, None if not"""
    if not credentials:
        return None

    try:
        token_data = await validate_token_with_auth_service(credentials.credentials)
        return token_data
    except:
        return None