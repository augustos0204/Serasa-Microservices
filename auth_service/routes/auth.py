from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from services.auth_service import AuthService
from schemas.auth_schemas import LoginRequest, LoginResponse
from schemas.user_schemas import UserResponse
from dependencies.auth_deps import get_current_user
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    auth_result = await AuthService.authenticate_user(db, login_data.email, login_data.password)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return auth_result

@router.get("/validate", status_code=status.HTTP_200_OK)
async def validate_token(
    current_user: User = Depends(get_current_user)
):
    return {"status": "valid"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_data(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.from_orm(current_user)