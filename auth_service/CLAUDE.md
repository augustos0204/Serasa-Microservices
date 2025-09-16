# CLAUDE.md - Auth Service

This file provides guidance to Claude Code when working with the Auth Service microservice.

## Service Overview

The Auth Service is responsible for JWT-based authentication and user management. It runs on port 8003 and provides stateless authentication for the ETL system.

## Dependencies Explained

### Core Framework
- **fastapi**: Modern, fast web framework for building APIs with automatic OpenAPI documentation and async support
- **uvicorn**: ASGI server for running FastAPI applications with high performance

### Authentication & Security
- **python-jose[cryptography]**: JWT token creation, validation, and cryptographic operations for secure authentication
- **pydantic**: Data validation and serialization for request/response models with type safety

### HTTP Client & Logging
- **httpx**: Async HTTP client for inter-service communication (if needed to validate with external services)
- **structlog**: Structured logging library for consistent, searchable logs in JSON format

## Key Responsibilities

- User authentication (login/password validation)
- JWT token generation with expiration
- Token validation for other services
- Permission-based access control
- User session management
- Security logging and audit trails

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run service locally
uvicorn main:app --reload --port 8003

# Run with Docker
docker build -t auth-service .
docker run -p 8003:8000 auth-service
```

## API Endpoints

### Authentication
- `POST /login` - User authentication and token generation

### User Management
- `POST /users/` - Create new user
- `GET /users/{user_id}` - Get user by ID
- `GET /users/` - List users with pagination
- `GET /users/email/{email}` - Get user by email
- `PATCH /users/{user_id}` - Update user information
- `DELETE /users/{user_id}` - Delete user

### System
- `GET /health` - Service health check
- `GET /docs` - OpenAPI documentation

## Environment Variables

**Required (must be in .env file):**
- `PORT`: Service port (no fallback allowed)
- `JWT_SECRET_KEY`: Secret key for JWT signing

**Optional (with fallbacks):**
- `HOST`: Service host (default: 0.0.0.0)
- `JWT_ALGORITHM`: Algorithm for JWT (default: HS256)  
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)

## Development Rules

**NEVER hardcode these values in code:**
- ❌ Ports (8003, 8001, 8002)
- ❌ External service URLs (http://localhost:8003)
- ❌ Secret keys, tokens, passwords
- ❌ Database connection strings
- ❌ API endpoints from other services

**ALWAYS use environment variables:**
- ✅ `os.getenv("PORT")` - Required, no fallback
- ✅ `os.getenv("HOST", "0.0.0.0")` - Optional with fallback
- ✅ `os.getenv("JWT_SECRET_KEY")` - Required for security
- ✅ `os.getenv("EXTERNAL_SERVICE_URL")` - For service communication

