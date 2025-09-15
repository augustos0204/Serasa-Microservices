import os
import httpx
from typing import Optional

class AuthConnectionService:
    def __init__(self):
        self.host = os.getenv("AUTH_SERVICE_HOST")
        self.port = int(os.getenv("AUTH_SERVICE_PORT"))
        self.base_url = f"http://{self.host}:{self.port}"

    async def test_connection(self) -> bool:
        try:
            print(f"🔐 Attempting to connect to Auth Service...")
            print(f"   📍 Host: {self.host}:{self.port}")

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)

                if response.status_code == 200:
                    print("✅ Auth Service connection successful!")
                    return True
                else:
                    print(f"❌ Auth Service connection failed - Status: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Auth Service connection failed: {str(e)}")
            return False

    async def get_connection_info(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "status": "checking..."
        }