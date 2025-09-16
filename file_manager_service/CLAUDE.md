# CLAUDE.md - File Manager Service

This file provides guidance to Claude Code when working with the File Manager Service microservice.

## Service Overview

The File Manager Service handles file upload/download operations and queue messaging. It runs on port 8001 and serves as the entry point for CSV files in the ETL pipeline.

## Dependencies Explained

### Core Framework
- **fastapi**: Modern, fast web framework with automatic OpenAPI docs and async support for file operations
- **uvicorn**: ASGI server for running FastAPI applications with high performance

### File Operations
- **aiofiles**: Async file I/O operations to prevent blocking during large file uploads/downloads
- **python-multipart**: Support for multipart/form-data file uploads in FastAPI

### Message Queue
- **aio-pika**: Async RabbitMQ client for sending file metadata to processing queue with FIFO guarantees

### HTTP & Validation
- **httpx**: Async HTTP client for authentication validation with Auth Service
- **pydantic**: Data validation and serialization for file metadata and API models

## Key Responsibilities

- CSV file upload handling
- File download with authentication
- File storage management (`/files/` directory structure)
- Queue message publishing (file metadata to RabbitMQ)
- JWT token validation via Auth Service
- File access logging and audit

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run service locally
uvicorn main:app --reload --port 8001

# Run with Docker
docker build -t file-manager-service .
docker run -p 8001:8000 -v ./files:/app/files file-manager-service
```

## API Endpoints

- `POST /upload` - File upload with authentication
- `GET /download/{file_id}` - Authenticated file download
- `GET /files` - List uploaded files (authenticated)
- `GET /health` - Service health check
- `GET /docs` - OpenAPI documentation

## File Storage Structure

```
/files/
├── original/     # Uploaded files
├── processed/    # Successfully processed files
└── failed/       # Failed processing files
```

## Environment Variables

**Required (must be in .env file):**
- `PORT`: Service port (no fallback allowed)
- `RABBITMQ_URL`: RabbitMQ connection string
- `AUTH_SERVICE_URL`: Auth Service URL for token validation

**Optional (with fallbacks):**
- `HOST`: Service host (default: 0.0.0.0)
- `UPLOAD_DIR`: Directory for file storage (default: /app/files)

## Development Rules

**NEVER hardcode these values in code:**
- ❌ Ports (8003, 8001, 8002)
- ❌ External service URLs (http://localhost:8003)
- ❌ RabbitMQ URLs (amqp://admin:admin123@localhost:5672/)
- ❌ File storage paths (/app/files)
- ❌ Database connection strings
- ❌ Queue names and configuration

**ALWAYS use environment variables:**
- ✅ `os.getenv("PORT")` - Required, no fallback
- ✅ `os.getenv("HOST", "0.0.0.0")` - Optional with fallback
- ✅ `os.getenv("RABBITMQ_URL")` - Required for queue operations
- ✅ `os.getenv("AUTH_SERVICE_URL")` - Required for token validation
- ✅ `os.getenv("UPLOAD_DIR", "/app/files")` - Optional with fallback