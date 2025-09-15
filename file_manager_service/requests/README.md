# Requests - Example Creation Guide

This directory contains `.http` files to test APIs using VS Code REST Client extension.

## Structure of an .http file

Each file should contain all requests related to a functionality:

```http
### Basic GET Request
GET http://localhost:PORT/endpoint
Content-Type: application/json

###

### POST Request with JSON Body
POST http://localhost:PORT/endpoint
Content-Type: application/json

{
    "field1": "value1",
    "field2": "value2"
}

###

### Authenticated Request
GET http://localhost:PORT/protected-endpoint
Authorization: Bearer TOKEN

###

### Request with Query Parameters
GET http://localhost:PORT/endpoint?param1=value1&param2=value2

###

### PUT Request
PUT http://localhost:PORT/endpoint/123
Content-Type: application/json
Authorization: Bearer TOKEN

{
    "field1": "updated_value"
}

###

### File Upload (multipart)
POST http://localhost:PORT/upload
Authorization: Bearer TOKEN
Content-Type: multipart/form-data; boundary=boundary

--boundary
Content-Disposition: form-data; name="file"; filename="example.csv"
Content-Type: text/csv

field1,field2,field3
value1,value2,value3
--boundary--

###

### Health Check
GET http://localhost:PORT/health
```

## Organization Structure

### Separators
Use `###` to separate different requests:

```http
### Descriptive request name
POST http://localhost:PORT/endpoint
Content-Type: application/json

{
    "data": "example"
}

###
```

### Variables
Use variables to reuse values:

```http
@baseUrl = http://localhost:PORT
@token = your-jwt-token-here

### Login
POST {{baseUrl}}/endpoint
Content-Type: application/json

{
    "field1": "value1"
}

### Protected Request
GET {{baseUrl}}/protected
Authorization: Bearer {{token}}
```

### Environments
Create separate files for different environments:

- `service_local.http` - Local environment
- `service_dev.http` - Development environment  
- `service_prod.http` - Production environment

## Best Practices

1. **Clear Naming**: Use descriptive names for each request
2. **Documentation**: Add comments explaining special parameters
3. **Test Data**: Use realistic but fictional data
4. **Logical Order**: Organize requests in order of use
5. **Dynamic Tokens**: Clearly indicate where to replace tokens/IDs

## Complete Example

```http
# File: service_requests.http
# Tests for Service

@baseUrl = http://localhost:PORT

### 1. Health Check
GET {{baseUrl}}/health

### 2. Create Resource
# @name create
POST {{baseUrl}}/resource
Content-Type: application/json

{
    "name": "test resource",
    "description": "example description"
}

### 3. Get Resource
GET {{baseUrl}}/resource/{{create.response.body.id}}

### 4. Invalid Request - Should return 400
POST {{baseUrl}}/resource
Content-Type: application/json

{
    "invalid": "data"
}
```

## File naming

- Use `snake_case` for file names
- Be descriptive: `service_requests.http`, `operations.http`
- Group related requests in the same file