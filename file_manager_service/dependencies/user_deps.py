from fastapi import Request, HTTPException
from services.user_service import UserService, UserData


async def get_current_user_from_request(request: Request) -> UserData:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = auth_header.split(" ")[1]

    user_data = await UserService.get_user_data(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Unable to get user data")

    return user_data