from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
import os
from typing import Optional

from services.user_service import UserService

class AuthService:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))

        to_encode.update({"exp": expire})
        secret_key = os.getenv("JWT_SECRET_KEY")
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        return encoded_jwt

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[dict]:
        user = await UserService.authenticate_user(db, email, password)
        if not user:
            return None

        access_token = AuthService.create_access_token(data={"user_id": user.id})

        return {
            "user_token": access_token,
            "token_type": "bearer",
            "user_id": user.id
        }

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        try:
            secret_key = os.getenv("JWT_SECRET_KEY")
            algorithm = os.getenv("JWT_ALGORITHM", "HS256")

            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            user_id: int = payload.get("user_id")
            if user_id is None:
                return None
            return {"user_id": user_id}
        except JWTError:
            return None