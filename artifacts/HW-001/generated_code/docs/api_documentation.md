# Hello World API Documentation

Complete API reference for the Hello World REST API built with FastAPI.

## Base URL

```
http://localhost:8000
```

## Overview

The Hello World API is a simple REST service that provides greeting functionality and health monitoring. It features two endpoints with JSON responses and comprehensive error handling.

## Authentication

No authentication is required for any endpoints in this API.

## Rate Limiting

No rate limiting is currently implemented.

## Content Type

All endpoints return JSON responses with `Content-Type: application/json`.

## Error Response Format

All error responses follow a consistent structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description"
  }
}
```

## Endpoints

### GET /hello

Returns a greeting message with optional personalization.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `name` | string | query | No | Name to personalize greeting (max 100 chars, alphanumeric and spaces only) |

#### Request Examples

**Basic greeting:**
```http
GET /hello HTTP/1.1
Host: localhost:8000
```

**Personalized greeting:**
```http
GET /hello?name=Alice HTTP/1.1
Host: localhost:8000
```

**Multiple word name:**
```http
GET /hello?name=John%20Doe HTTP/1.1
Host: localhost:8000
```

#### Response Examples

**Success Response (200 OK) - Default:**
```json
{
  "message": "Hello, World!"
}
```

**Success Response (200 OK) - Personalized:**
```json
{
  "message": "Hello, Alice!"
}
```

#### Error Responses

**400 Bad Request - Invalid Name Characters:**
```json
{
  "error": {
    "code": "INVALID_NAME",
    "message": "Name parameter contains invalid characters or exceeds 100 characters"
  }
}
```

**Example invalid requests:**
- `GET /hello?name=Alice@123` (contains special characters)
- `GET /hello?name=<script>alert('xss')</script>` (contains HTML/script tags)
- `GET /hello?name=` + 101 character string (exceeds length limit)

**500 Internal Server Error:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Success - greeting returned |
| 400 | Bad Request - invalid name parameter |
| 500 | Internal Server Error - unexpected server error |

#### Validation Rules

- **Name parameter validation:**
  - Optional parameter (can be omitted)
  - Maximum length: 100 characters
  - Allowed characters: letters (a-z, A-Z), numbers (0-9), and spaces
  - Empty string treated as no name provided
  - Leading/trailing spaces are preserved

### GET /health

Returns application health status and current timestamp for monitoring purposes.

#### Parameters

None.

#### Request Example

```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### Response Examples

**Success Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:45.123456Z"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always returns "ok" when service is running |
| `timestamp` | string | Current UTC timestamp in ISO 8601 format |

#### Error Responses

**500 Internal Server Error:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Success - health status returned |
| 500 | Internal Server Error - unexpected server error |

#### Timestamp Format

The timestamp follows ISO 8601 format in UTC timezone:
- Format: `YYYY-MM-DDTHH:MM:SS.fffffZ`
- Example: `2024-01-15T10:30:45.123456Z`
- Always ends with 'Z' indicating UTC timezone

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

## cURL Examples

### Hello Endpoint Examples

**Basic greeting:**
```bash
curl -X GET "http://localhost:8000/hello"
```

**Personalized greeting:**
```bash
curl -X GET "http://localhost:8000/hello?name=Alice"
```

**Name with spaces:**
```bash
curl -X GET "http://localhost:8000/hello?name=John%20Doe"
```

### Health Endpoint Example

```bash
curl -X GET "http://localhost:8000/health"
```

## HTTP Client Examples

### Python (requests)

```python
import requests

# Basic greeting
response = requests.get("http://localhost:8000/hello")
print(response.json())  # {"message": "Hello, World!"}

# Personalized greeting
response = requests.get("http://localhost:8000/hello", params={"name": "Alice"})
print(response.json())  # {"message": "Hello, Alice!"}

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())  # {"status": "ok", "timestamp": "2024-01-15T10:30:45.123456Z"}
```

### JavaScript (fetch)

```javascript
// Basic greeting
fetch('http://localhost:8000/hello')
  .then(response => response.json())
  .then(data => console.log(data)); // {message: "Hello, World!"}

// Personalized greeting
fetch('http://localhost:8000/hello?name=Alice')
  .then(response => response.json())
  .then(data => console.log(data)); // {message: "Hello, Alice!"}

// Health check
fetch('http://localhost:8000/health')
  .then(response => response.json())
  .then(data => console.log(data)); // {status: "ok", timestamp: "2024-01-15T10:30:45.123456Z"}
```

## Error Handling Best Practices

### Client-Side Error Handling

Always check the HTTP status code and handle errors appropriately:

```python
import requests

response = requests.get("http://localhost:8000/hello", params={"name": "Invalid@Name"})

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data['message']}")
elif response.status_code == 400:
    error = response.json()
    print(f"Validation Error: {error['error']['message']}")
elif response.status_code == 500:
    error = response.json()
    print(f"Server Error: {error['error']['message']}")
else:
    print(f"Unexpected status code: {response.status_code}")
```

### Common Error Scenarios

1. **Invalid Name Characters:**
   - Names containing symbols: `!@#$%^&*()`
   - Names containing HTML/XML tags: `<script>`, `<div>`
   - Names containing newlines or control characters

2. **Name Length Validation:**
   - Names longer than 100 characters will be rejected
   - Empty names are allowed and treated as no name provided

3. **Server Errors:**
   - Network connectivity issues
   - Server overload or maintenance
   - Unexpected application errors

## Monitoring and Health Checks

The `/health` endpoint is designed for monitoring systems and load balancers:

### Health Check Integration

**Docker Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit