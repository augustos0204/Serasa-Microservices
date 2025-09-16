# CLAUDE.md - Data Processor Service

This file provides guidance to Claude Code when working with the Data Processor Service microservice.

## Service Overview

The Data Processor Service handles CSV processing, data validation, and database persistence. It runs on port 8002 and processes files asynchronously from the RabbitMQ queue.

## Dependencies Explained

### Core Framework
- **fastapi**: Modern, fast web framework with async support for background processing and API endpoints
- **uvicorn**: ASGI server for running FastAPI applications with high performance

### Database & ORM
- **sqlalchemy[asyncio]**: Async ORM for PostgreSQL operations with connection pooling and query optimization
- **asyncpg**: High-performance async PostgreSQL driver for SQLAlchemy

### Data Processing
- **pandas**: Powerful data manipulation and analysis library for CSV processing and transformations
- **pandera**: Data validation framework for pandas DataFrames with schema enforcement

### File & Queue Operations
- **aiofiles**: Async file I/O operations to prevent blocking during CSV reading/writing
- **aio-pika**: Async RabbitMQ consumer for processing file metadata from queue

### Security & Validation
- **cryptography**: AES-256 encryption for sensitive data (email, CPF, phone) before database storage
- **pydantic**: Data validation and serialization for API models and database schemas

## Key Responsibilities

- RabbitMQ queue consumption (FIFO processing)
- CSV file parsing and validation
- Data transformation and normalization
- Duplicate detection and removal
- Sensitive data encryption (AES-256)
- PostgreSQL data persistence
- Inconsistency tracking and logging
- Background processing with retry mechanisms

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run service locally
uvicorn main:app --reload --port 8002

# Run with Docker
docker build -t data-processor-service .
docker run -p 8002:8000 data-processor-service
```

## API Endpoints

- `POST /process` - Manual file processing trigger
- `GET /file-inconsistencies` - Query processing inconsistencies by file_id
- `GET /processing-status/{file_id}` - Check file processing status
- `GET /health` - Service health check
- `GET /docs` - OpenAPI documentation

## Database Tables

- **users**: Processed user data with encrypted sensitive fields
- **file_inconsistencies**: Data validation errors and invalid records
- **file_processing_log**: Processing status, metrics, and error details

## Environment Variables

**Required (must be in .env file):**
- `PORT`: Service port (no fallback allowed)
- `DATABASE_URL`: PostgreSQL connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `ENCRYPTION_KEY`: AES-256 key for sensitive data encryption

**Optional (with fallbacks):**
- `HOST`: Service host (default: 0.0.0.0)
- `PROCESSED_DIR`: Directory for processed files (default: /app/files/processed)
- `FAILED_DIR`: Directory for failed files (default: /app/files/failed)
- `RETRY_ATTEMPTS`: Maximum retry attempts (default: 3)

## Development Rules

**NEVER hardcode these values in code:**
- ❌ Ports (8003, 8001, 8002)
- ❌ Database URLs (postgresql://user:pass@localhost:5432/db)
- ❌ RabbitMQ URLs (amqp://admin:admin123@localhost:5672/)
- ❌ Encryption keys and secrets
- ❌ File storage paths (/app/files/processed)
- ❌ Queue names and retry configurations
- ❌ External service endpoints

**ALWAYS use environment variables:**
- ✅ `os.getenv("PORT")` - Required, no fallback
- ✅ `os.getenv("HOST", "0.0.0.0")` - Optional with fallback
- ✅ `os.getenv("DATABASE_URL")` - Required for database operations
- ✅ `os.getenv("RABBITMQ_URL")` - Required for queue operations
- ✅ `os.getenv("ENCRYPTION_KEY")` - Required for data security
- ✅ `os.getenv("RETRY_ATTEMPTS", "3")` - Optional with fallback