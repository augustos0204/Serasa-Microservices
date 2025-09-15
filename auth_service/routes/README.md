# Routes - Creation Example Guide

This directory contains all application routes organized by functionality.

## Route file structure

Each route file should follow this pattern:

```python
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from services.example_service import ExampleService
from pydantic import BaseModel
from typing import List

router = APIRouter()
security = HTTPBearer()  # If authentication is needed

# Pydantic models for request/response
class ExampleRequest(BaseModel):
    field1: str
    field2: int

class ExampleResponse(BaseModel):
    id: str
    message: str

# Basic route
@router.get("/", response_model=List[ExampleResponse])
async def get_examples():
    """Description of what the route does"""
    service = ExampleService()
    return await service.get_all()

# Route with parameter
@router.get("/{item_id}", response_model=ExampleResponse)
async def get_example(item_id: str):
    """Get specific item"""
    service = ExampleService()
    result = await service.get_by_id(item_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return result

# Route with authentication (if needed)
@router.post("/", response_model=ExampleResponse)
async def create_example(
    request: ExampleRequest, 
    token: str = Depends(security)
):
    """Create new item with authentication"""
    # Validate token if needed
    service = ExampleService()
    return await service.create(request)
```

## File naming

- Use `snake_case` for file names
- Be descriptive: `resource_routes.py`, `service_routes.py`
- Group related functionalities in the same file

## Integration with router.py

After creating a route, add it to `router.py`:

```python
from routes import example_routes

router.include_router(
    example_routes.router, 
    prefix="/examples", 
    tags=["examples"]
)
```