import argparse
import os
import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from router import router
from services.database_connection_service import DatabaseConnectionService
from middleware import ExceptionHandlerMiddleware

load_dotenv()

class ServiceConfig:
    def __init__(self, service_name: str, service_description: str):
        self.service_name = service_name
        self.service_description = service_description
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT"))
    
    def create_app(self) -> FastAPI:
        app = FastAPI(
            title=self.service_name,
            description=self.service_description,
            version="1.0.0"
        )

        app.add_middleware(ExceptionHandlerMiddleware)

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        return app
    
    async def print_startup_logs(self, mode: str):
        mode_text = "DEVELOPMENT" if mode == "dev" else "PRODUCTION"
        print(f"🚀 Starting {self.service_name} in {mode_text} mode")
        print(f"📍 Server: http://localhost:{self.port}")

        if mode == "dev":
            print(f"📚 API Docs: http://localhost:{self.port}/docs")
            print("🔄 Hot reload: ENABLED")

        print("\n🔍 Testing external connections...")

        db_service = DatabaseConnectionService()
        await db_service.test_connection()

        print("✨ Connection tests completed\n")
    
    def get_uvicorn_config(self, mode: str) -> dict:
        return {
            "app": "main:app",
            "host": self.host,
            "port": self.port,
            "reload": mode == "dev"
        }

config = ServiceConfig(
    service_name="Auth Service",
    service_description="JWT Authentication and Authorization Service"
)

app = config.create_app()
app.include_router(router)

async def startup():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="prod", help="Running mode: dev or prod")
    args = parser.parse_args()

    await config.print_startup_logs(args.mode)
    uvicorn_config = config.get_uvicorn_config(args.mode)
    uvicorn.run(**uvicorn_config)

if __name__ == "__main__":
    asyncio.run(startup())