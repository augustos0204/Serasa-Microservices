from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from models.database import get_db
from services.auth_service import AuthService
from services.user_service import UserService
from models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token_data = AuthService.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception

    user_id = token_data.get("user_id")
    if user_id is None:
        raise credentials_exception

    user = await UserService.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None

    try:
        token_data = AuthService.verify_token(credentials.credentials)
        if token_data is None:
            return None

        user_id = token_data.get("user_id")
        if user_id is None:
            return None

        user = await UserService.get_user_by_id(db, user_id)
        return user
    except:
        return None

def require_user_access(user_id: int):
    async def check_user_access(current_user: User = Depends(get_current_user)) -> User:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this user's data"
            )
        return current_user
    return check_user_access