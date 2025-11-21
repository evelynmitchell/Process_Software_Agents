# Hello World API Documentation

Complete API reference for the Hello World REST API built with FastAPI.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Configure based on deployment

## API Overview

The Hello World API provides two simple endpoints:
- `/hello` - Returns personalized or default greeting messages
- `/health` - Returns application health status and timestamp

All responses are in JSON format with appropriate HTTP status codes.

## Authentication

No authentication is required for any endpoints in this API.

## Rate Limiting

No rate limiting is currently implemented.

## Content Type

All API responses return `application/json` content type.

## Error Response Format

All error responses follow a consistent JSON structure:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error description"
}
```

## Endpoints

### GET /hello

Returns a greeting message with optional personalization.

#### Request

**URL**: `/hello`  
**Method**: `GET`  
**Authentication**: None required

#### Query Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `name` | string | No | Name to personalize greeting | Max 100 characters, alphanumeric and spaces only |

#### Request Examples

**Basic greeting (no parameters):**
```http
GET /hello HTTP/1.1
Host: localhost:8000
```

**Personalized greeting:**
```http
GET /hello?name=John HTTP/1.1
Host: localhost:8000
```

**Personalized greeting with spaces:**
```http
GET /hello?name=John%20Doe HTTP/1.1
Host: localhost:8000
```

#### Response

**Success Response (200 OK)**

```json
{
  "message": "Hello, World!"
}
```

**Success Response with name parameter (200 OK)**

```json
{
  "message": "Hello, John!"
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Greeting message, either default or personalized |

#### Error Responses

**400 Bad Request - Invalid Name Parameter**

Returned when the name parameter contains invalid characters or exceeds length limit.

```json
{
  "code": "INVALID_NAME",
  "message": "Name parameter contains invalid characters or exceeds 100 characters"
}
```

**Triggers:**
- Name contains characters other than letters, numbers, and spaces
- Name exceeds 100 characters
- Name contains special characters or symbols

**500 Internal Server Error**

```json
{
  "code": "INTERNAL_ERROR",
  "message": "Internal server error"
}
```

#### cURL Examples

**Basic greeting:**
```bash
curl -X GET "http://localhost:8000/hello"
```

**Personalized greeting:**
```bash
curl -X GET "http://localhost:8000/hello?name=Alice"
```

**Test invalid name (should return 400):**
```bash
curl -X GET "http://localhost:8000/hello?name=John@Doe"
```

### GET /health

Returns application health status and current timestamp for monitoring purposes.

#### Request

**URL**: `/health`  
**Method**: `GET`  
**Authentication**: None required

#### Query Parameters

None

#### Request Example

```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### Response

**Success Response (200 OK)**

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:45.123456Z"
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always returns "ok" for this simple health check |
| `timestamp` | string | Current UTC timestamp in ISO 8601 format with Z suffix |

#### Error Responses

**500 Internal Server Error**

```json
{
  "code": "INTERNAL_ERROR",
  "message": "Internal server error"
}
```

#### cURL Example

```bash
curl -X GET "http://localhost:8000/health"
```

## Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input parameters |
| 500 | Internal Server Error | Unexpected server error |

## Input Validation Rules

### Name Parameter Validation

The `name` query parameter in the `/hello` endpoint follows these validation rules:

1. **Character Set**: Only alphanumeric characters (a-z, A-Z, 0-9) and spaces are allowed
2. **Length Limit**: Maximum 100 characters
3. **Processing**: Leading/trailing whitespace is automatically trimmed
4. **Case Handling**: Name is converted to title case (first letter of each word capitalized)

**Valid Examples:**
- `John`
- `John Doe`
- `Alice123`
- `Bob Smith Jr`

**Invalid Examples:**
- `John@Doe` (contains special character @)
- `Alice-Bob` (contains hyphen)
- `John_Doe` (contains underscore)
- Names longer than 100 characters

## Error Handling

The API implements comprehensive error handling with consistent JSON responses:

### Validation Errors (400)

Triggered by invalid input parameters. The API validates all inputs and returns descriptive error messages.

### HTTP Exceptions

The API properly handles and formats HTTP exceptions while preserving the original status codes.

### Internal Errors (500)

Unexpected server errors are caught and logged, returning a generic error message to prevent information disclosure.

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## CORS Configuration

The API is configured with CORS (Cross-Origin Resource Sharing) enabled for all origins in development mode:

- **Allowed Origins**: `*` (all origins)
- **Allowed Methods**: `GET` (only GET methods are implemented)
- **Allowed Headers**: Standard headers

## Response Times

Expected response times for each endpoint:

- `/hello`: < 10ms (simple string processing)
- `/health`: < 5ms (timestamp generation only)

## Monitoring and Observability

### Health Checks

Use the `/health` endpoint for:
- Load balancer health checks
- Container orchestration health probes
- Monitoring system status verification

The endpoint returns:
- Consistent "ok" status
- Current UTC timestamp for request tracking
- 200 status code for successful health checks

### Logging

The application logs the following events:
- Request validation errors (400 responses)
- Internal server errors (500 responses)
- Application startup and shutdown events

## Development and Testing

### Testing the API

**Test successful greeting:**
```bash
# Should return: {"message": "Hello, World!"}
curl "http://localhost:8000/hello"
```

**Test personalized greeting:**
```bash
# Should return: {"message": "Hello, Alice!"}
curl "http://localhost:8000/hello?name=Alice"
```

**Test input validation:**
```bash
# Should return 400 error
curl "http://localhost:8000/hello?name=Invalid@Name"
```

**Test health endpoint:**
```bash
# Should return status and timestamp
curl "http://localhost:8000/health"
```

### Common Integration Patterns

**JavaScript/Frontend Integration:**
```javascript
// Fetch greeting
const response = await fetch('/hello?name=User');
const data = await response.json();
console.log(data.message); // "Hello, User!"

// Health check
const health = await fetch('/health');
const healthData = await health.json();
console.log(healthData.status); // "ok"
```

**Python Client Integration:**
```python
import requests

# Get greeting
response = requests.get('http://localhost:8000/hello', params={'name': 'Python'})
print(response.json()['message'])  # "Hello, Python!"

# Health check
health = requests.get('http://localhost:8000/health')
print(health.json()['status'])  # "ok"
```

## Troubleshooting

### Common Issues

**Issue**: