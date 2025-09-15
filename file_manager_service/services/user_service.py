import httpx
import os
from typing import Optional
from pydantic import BaseModel


class UserData(BaseModel):
    id: int
    email: str
    full_name: str


class UserService:
    @staticmethod
    async def get_user_data(token: str) -> Optional[UserData]:
        auth_service_url = os.getenv("AUTH_SERVICE_URL")
        if not auth_service_url:
            raise ValueError("AUTH_SERVICE_URL environment variable not set")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{auth_service_url}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0
                )

                if response.status_code == 200:
                    user_data = response.json()
                    return UserData(**user_data)
                else:
                    return None

        except Exception:
            return None