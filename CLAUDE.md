# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ETL system technical challenge implementing secure, asynchronous, and scalable APIs with queue-based processing. The system consists of 3 microservices:

1. **Auth Service** (Port 8003) - JWT authentication and authorization (`./auth_service`)
2. **File Manager Service** (Port 8001) - File upload/download with queue messaging (`./file_manager_service`)
3. **Data Processor Service** (Port 8002) - CSV processing and inconsistency tracking (`./data_processor_service`)

## Architecture

The system follows a microservices architecture with:
- **FastAPI** for all services (async, performance, OpenAPI docs)
- **PostgreSQL** database for data persistence
- **RabbitMQ** message broker for FIFO queue processing
- **Docker Compose** for container orchestration
- **JWT** for stateless authentication
- **AES-256 encryption** for sensitive data (bonus feature)

### Service Technology Stack

**Auth Service (Port 8003):**
```python
fastapi==0.104.1
python-jose[cryptography]==3.3.0
pydantic==2.5.0
structlog==23.2.0
httpx==0.25.2
```

**File Manager Service (Port 8001):**
```python
fastapi==0.104.1
aiofiles==23.2.0
python-multipart==0.0.6
aio-pika==9.3.1
httpx==0.25.2
pydantic==2.5.0
```

**Data Processor Service (Port 8002):**
```python
fastapi==0.104.1
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
pandas==2.1.3
aio-pika==9.3.1
pandera==0.17.2
cryptography==41.0.8
aiofiles==23.2.0
```

## Development Commands

**IMPORTANT: This project uses `uv` as the package manager for all Python services.**

### Package Management
```bash
# Install dependencies (use uv instead of pip)
uv pip install -r requirements.txt

# Add new dependency
uv add package-name

# Run Python scripts
uv run python main.py --mode=dev
```

### Database Management

**This project uses PostgreSQL init.sql for database schema management instead of Alembic migrations.**

#### Benefits of init.sql Approach:
- ✅ **Zero Migration Conflicts**: No revision ID conflicts between microservices
- ✅ **Atomic Setup**: Database is created in a single, consistent state
- ✅ **Simpler Development**: No complex migration dependency chains
- ✅ **Faster Startup**: No sequential migration containers needed
- ✅ **Predictable State**: Same schema every time, no migration history issues
- ✅ **Cross-Service Relations**: Foreign keys work naturally without migration ordering
- ✅ **Easy Reset**: Complete database reset with single command

#### Key Files:
- **Schema Definition**: All database tables are defined in `/init.sql`
- **Automatic Setup**: PostgreSQL runs `init.sql` automatically on first startup
- **Sample Data**: Includes development user for testing

```bash
# Database is automatically initialized when PostgreSQL starts
# No manual migration commands needed

# To reset database completely:
docker compose -f docker-compose.dev-simplified.yml down -v
docker compose -f docker-compose.dev-simplified.yml up -d postgres

# Check initialization status:
docker logs etl_postgres_dev | grep "init.sql"
```

### Infrastructure Setup

**Both development and production environments use the same init.sql approach for database setup.**

#### Development Environment
- **File**: `docker-compose.dev-simplified.yml`
- **Features**: Direct port access, volume mounts for hot reload
- **Database**: Fresh init.sql execution on each reset
```bash
# Start all services (simplified - no migrations)
docker compose -f docker-compose.dev-simplified.yml up -d

# Start only infrastructure (PostgreSQL + RabbitMQ)
docker compose -f docker-compose.dev-simplified.yml up -d postgres rabbitmq

# View logs (container names)
docker compose -f docker-compose.dev-simplified.yml logs -f etl_postgres_dev      # PostgreSQL
docker compose -f docker-compose.dev-simplified.yml logs -f etl_rabbitmq_dev      # RabbitMQ
docker compose -f docker-compose.dev-simplified.yml logs -f etl_file_manager_dev  # File Manager Service
docker compose -f docker-compose.dev-simplified.yml logs -f etl_data_processor_dev # Data Processor Service
docker compose -f docker-compose.dev-simplified.yml logs -f etl_auth_dev          # Auth Service

# Stop services
docker compose -f docker-compose.dev-simplified.yml down

# Reset everything (including database)
docker compose -f docker-compose.dev-simplified.yml down -v
```

#### Production Environment with Load Balancer
- **File**: `docker-compose.yml`
- **Features**: Nginx load balancer, horizontal scaling, no direct port access
- **Database**: Same init.sql automatic setup
- **Access**: All requests through Nginx on port 80
```bash
# Start all services with Nginx load balancer
docker compose up -d

# Start only infrastructure
docker compose up -d postgres rabbitmq nginx

# View logs (container names)
docker compose logs -f etl_postgres         # PostgreSQL
docker compose logs -f etl_rabbitmq         # RabbitMQ
docker compose logs -f etl_nginx             # Nginx Load Balancer
docker compose logs -f auth-service          # Auth Service
docker compose logs -f file-manager-service  # File Manager Service
docker compose logs -f data-processor-service # Data Processor Service

# Scale services horizontally
docker compose up --scale auth-service=2 --scale file-manager-service=3 --scale data-processor-service=2 -d

# Stop services
docker compose down

# Reset everything (including database)
docker compose down -v
```

## Development Rules - Environment Variables

**CRITICAL: Never hardcode configuration values in code**

### Values that MUST be in .env files:
- ❌ **Ports**: Never use `8001`, `8002`, `8003` in code
- ❌ **URLs**: Never use `http://localhost:8003` in code  
- ❌ **Secrets**: Never use hardcoded JWT keys, passwords, tokens
- ❌ **Connections**: Never use hardcoded database/queue URLs
- ❌ **Paths**: Never use hardcoded file storage paths

### Correct pattern:
```python
# ✅ CORRECT - Always use environment variables
port = int(os.getenv("PORT"))  # Required, no fallback
host = os.getenv("HOST", "0.0.0.0")  # Optional with fallback
auth_url = os.getenv("AUTH_SERVICE_URL")  # Required for external services

# ❌ WRONG - Never hardcode
port = 8003  # Wrong!
auth_url = "http://localhost:8003"  # Wrong!
```

### Each service .env must define:
- `PORT` - Service port (required)
- `HOST` - Service host (optional, defaults to 0.0.0.0)  
- Service-specific URLs, secrets, and paths (required)

### Service Health Checks
```bash
# Check Auth Service
curl http://localhost:8003/health

# Check File Manager Service  
curl http://localhost:8001/health

# Check Data Processor Service
curl http://localhost:8002/health
```

### API Documentation
- **Load Balancer**: http://localhost (Nginx routes to services)
- Auth Service: http://localhost/auth/docs
- File Manager Service: http://localhost/files/docs
- Data Processor Service: http://localhost/process/docs
- RabbitMQ Management: http://localhost:15672 (admin/admin123)

### Horizontal Scaling with Load Balancer
```bash
# Start with load balancer
docker-compose up -d

# Scale services horizontally
docker-compose up --scale auth-service=2 --scale file-manager-service=3 --scale data-processor-service=2 -d

# Check scaled instances
docker-compose ps

# Access via load balancer (port 80)
curl http://localhost/health              # Nginx health
curl http://localhost/auth/health         # Auth service
curl http://localhost/files/health        # File Manager
curl http://localhost/process/health      # Data Processor
```

### Load Balancer Routes
- `/auth/` → Auth Service (JWT, users)
- `/files/` → File Manager Service (upload/download)
- `/process/` → Data Processor Service (CSV processing)
- `/file-inconsistencies/` → Data Processor Service (inconsistencies API)
- `/health` → Load balancer status

## Key Files

- `docker-compose.yml` - Complete infrastructure setup
- `usuarios.csv` - Sample CSV file with test data (includes invalid records)
- `docs/arquitetira_sistema_etl.md` - Detailed architecture documentation
- `scripts/init.sql/` - Database initialization scripts

## Database Schema

The system uses PostgreSQL with these main tables:

```sql
-- Usuários processados
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    encrypted_data JSONB,      -- Dados criptografados
    file_id VARCHAR(255),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Inconsistências encontradas
CREATE TABLE file_inconsistencies (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(255),
    line_number INTEGER,
    field_name VARCHAR(100),
    invalid_value TEXT,
    error_message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Log de processamentos
CREATE TABLE file_processing_log (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(255),
    status VARCHAR(50),
    records_processed INTEGER,
    records_invalid INTEGER,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    error_details JSONB
);
```

## Security Features

- JWT-based authentication with expiration
- Permission-based access control
- AES-256 encryption for sensitive data (email, CPF, phone)
- Internal Docker network isolation
- CORS configuration

## Development Notes

- The APIs are commented out in docker-compose.yml - they need to be implemented
- Sample CSV includes intentionally invalid data for testing inconsistency detection
- All services use async/await patterns for performance
- RabbitMQ ensures FIFO processing order
- Structured logging for observability
- Background task processing for non-blocking responses

### RabbitMQ Configuration
- **Main Queue**: `file_processing` (FIFO processing)
- **Retry Queue**: `file_processing_retry` (30s delay)
- **Dead Letter**: `file_processing_failed` (max retries exceeded)

### File Storage Structure
```
/files/
├── original/     # Uploaded files
├── processed/    # Successfully processed files
└── failed/       # Failed processing files
```

### Container Names
- Auth Service: `auth-service`
- File Manager Service: `file-manager-service`
- Data Processor Service: `data-processor-service`
- PostgreSQL: `etl_postgres`
- RabbitMQ: `etl_rabbitmq`

## ETL Flow

1. Client authenticates with Auth Service → receives JWT
2. Client uploads CSV to File Manager Service → validates JWT
3. File Manager Service stores file → sends metadata to RabbitMQ queue
4. Data Processor Service consumes queue → processes CSV asynchronously
5. Valid data encrypted and stored in PostgreSQL
6. Invalid data tracked in inconsistencies table
7. Client can query inconsistencies via GET /file-inconsistencies

## Testing Strategy

The system should include:
- Unit tests for CSV validation and transformation logic
- Integration tests for queue processing and database operations
- End-to-end tests for complete ETL workflow
- Authentication/authorization tests

## HTTP Request Files (.http)

**IMPORTANT**: All services should have request files in `/requests/` folder containing ONLY functional API calls:

### Rules for .http files:
- ✅ **Include**: Working requests with valid data
- ✅ **Include**: Basic CRUD operations examples
- ✅ **Include**: Authentication flows that succeed
- ✅ **Include**: Happy path scenarios for development testing
- ❌ **Exclude**: Error test cases (invalid data, wrong passwords, non-existent resources)
- ❌ **Exclude**: Validation failure examples
- ❌ **Exclude**: Authorization failure tests
- ❌ **Exclude**: Comments describing expected errors or failure scenarios

### Purpose:
- Quick testing during development
- API documentation by example
- Client integration reference
- Functional endpoint verification

### Standard Files per Service:
- `auth_requests.http` - Authentication endpoints (login, etc.)
- `user_requests.http` - User management CRUD operations
- `file_requests.http` - File upload/download operations
- `health_requests.http` - Health check endpoints

## Git Commit Guidelines

**IMPORTANT**: Use short, direct commit messages separated by feature and microservice:

### Commit Message Format:
```bash
# Feature-based commits by microservice
git add auth_service/models/ auth_service/services/auth_service.py
git commit -m "auth: add JWT authentication"

git add data_processor_service/services/csv_validation_service.py data_processor_service/models/file_inconsistencies.py
git commit -m "processor: add CSV validation and inconsistency tracking"

git add file_manager_service/routes/ file_manager_service/services/
git commit -m "file-manager: add file upload with queue messaging"
```

### Rules for git add:
- ✅ **Group by feature**: Add related files together (models + services + routes for same feature)
- ✅ **Separate by microservice**: Keep each service's changes in separate commits
- ✅ **Short commit messages**: Use format `service: feature description`
- ✅ **Direct language**: "add", "fix", "update", "remove"

### Examples:
```bash
# Good - grouped by feature and service
git add data_processor_service/models/file_inconsistencies.py data_processor_service/services/inconsistency_service.py data_processor_service/routes/file_inconsistencies.py
git commit -m "processor: add inconsistency tracking API"

# Good - infrastructure changes
git add docker-compose.yml .env.example
git commit -m "infra: add RabbitMQ and PostgreSQL setup"

# Good - documentation
git add CLAUDE.md docs/
git commit -m "docs: update development guidelines"
```