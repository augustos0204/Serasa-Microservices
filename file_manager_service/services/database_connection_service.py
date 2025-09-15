import os
import asyncpg
from typing import Optional

class DatabaseConnectionService:
    def __init__(self):
        self.host = os.getenv("DATABASE_HOST")
        self.port = int(os.getenv("DATABASE_PORT"))
        self.database = os.getenv("DATABASE_NAME")
        self.user = os.getenv("DATABASE_USER")
        self.password = os.getenv("DATABASE_PASSWORD")

    async def test_connection(self) -> bool:
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

            result = await conn.fetchval("SELECT 1")
            await conn.close()

            if result == 1:
                print("✅ PostgreSQL connection successful!")
                return True
            else:
                print("❌ PostgreSQL connection failed")
                return False

        except Exception as e:
            print(f"❌ PostgreSQL connection failed")
            return False

    async def get_connection_info(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "status": "checking..."
        }