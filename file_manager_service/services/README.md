# Services - Creation Example Guide

This directory contains all application business logic separated from routes.

## Service file structure

Each service file should follow this pattern:

```python
import os
from typing import Optional, List, Dict
from datetime import datetime

class ExampleService:
    def __init__(self):
        # Configuration and initialization
        self.config_value = os.getenv("CONFIG_VAR", "default_value")
        # Initialize connections, clients, etc.
    
    async def get_all(self) -> List[Dict]:
        """Get all items"""
        try:
            # Business logic here
            # Example: database query, external API, etc.
            return []
        except Exception as e:
            # Log error
            raise Exception(f"Error getting items: {str(e)}")
    
    async def get_by_id(self, item_id: str) -> Optional[Dict]:
        """Get item by ID"""
        try:
            # Input validation
            if not item_id or not item_id.strip():
                raise ValueError("ID is required")
            
            # Search logic
            # Returns None if not found
            return None
        except Exception as e:
            raise Exception(f"Error getting item {item_id}: {str(e)}")
    
    async def create(self, data: Dict) -> Dict:
        """Create new item"""
        try:
            # Business validation
            await self._validate_create_data(data)
            
            # Creation logic
            created_item = {
                "id": self._generate_id(),
                "created_at": datetime.utcnow().isoformat(),
                **data
            }
            
            return created_item
        except Exception as e:
            raise Exception(f"Error creating item: {str(e)}")
    
    async def update(self, item_id: str, data: Dict) -> Optional[Dict]:
        """Update existing item"""
        try:
            # Check if exists
            existing = await self.get_by_id(item_id)
            if not existing:
                return None
            
            # Update logic
            updated_item = {
                **existing,
                **data,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            return updated_item
        except Exception as e:
            raise Exception(f"Error updating item {item_id}: {str(e)}")
    
    async def delete(self, item_id: str) -> bool:
        """Delete item"""
        try:
            # Check if exists
            existing = await self.get_by_id(item_id)
            if not existing:
                return False
            
            # Deletion logic
            return True
        except Exception as e:
            raise Exception(f"Error deleting item {item_id}: {str(e)}")
    
    # Private helper methods
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def _validate_create_data(self, data: Dict) -> None:
        """Validate data for creation"""
        required_fields = ["field1", "field2"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field: {field}")
```

## Service Principles

1. **Separation of Concerns**: Each service handles a specific entity/domain
2. **Business Logic**: All business rules stay in services, not in routes
3. **Error Handling**: Services should handle and log errors properly
4. **Async/Await**: Use asynchronous operations for I/O (database, APIs, files)
5. **Validations**: Implement business validations in services
6. **Reusability**: Services can be used by multiple routes

## File naming

- Use `snake_case` for file names
- End with `_service.py`: `resource_service.py`, `data_service.py`
- Be descriptive about the domain/responsibility

## Dependency Injection

Services can use other services:

```python
from services.auth_service import AuthService
from services.database_service import DatabaseService

class BusinessService:
    def __init__(self):
        self.auth_service = AuthService()
        self.db_service = DatabaseService()
    
    async def get_protected_data(self, token: str):
        user = await self.auth_service.validate_token(token)
        return await self.db_service.get_data_by_user_id(user["id"])
```