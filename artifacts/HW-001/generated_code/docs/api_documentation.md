# Hello World API Documentation

Complete API documentation for the Hello World REST API built with FastAPI.

## Overview

The Hello World API is a simple REST service that provides greeting functionality and health monitoring. It features two main endpoints for generating personalized greetings and checking application health status.

**Base URL:** `http://localhost:8000`

**API Version:** 1.0.0

**Content Type:** `application/json`

## Authentication

This API does not require authentication. All endpoints are publicly accessible.

## Rate Limiting

No rate limiting is currently implemented on any endpoints.

## Error Response Format

All error responses follow a consistent JSON structure:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error description"
}
```

## Global Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | VALIDATION_ERROR | Request validation failed |
| 500 | INTERNAL_ERROR | Internal server error |

## Endpoints

### GET /hello

Returns a greeting message with optional personalization.

**Description:** Generates a greeting message. If a name parameter is provided, the greeting will be personalized. The name parameter is validated to ensure it contains only alphanumeric characters and spaces, with a maximum length of 100 characters.

**Parameters:**

| Parameter | Type | Required | Location | Description | Constraints |
|-----------|------|----------|----------|-------------|-------------|
| name | string | No | Query | Name to personalize the greeting | Max 100 chars, alphanumeric and spaces only |

**Request Examples:**

Basic greeting request:
```http
GET /hello HTTP/1.1
Host: localhost:8000
```

Personalized greeting request:
```http
GET /hello?name=John HTTP/1.1
Host: localhost:8000
```

Personalized greeting with spaces:
```http
GET /hello?name=John%20Doe HTTP/1.1
Host: localhost:8000
```

**Response Schema:**

```json
{
  "message": "string"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| message | string | The greeting message |

**Success Response Examples:**

Default greeting (no name parameter):
```json
{
  "message": "Hello, World!"
}
```

Personalized greeting:
```json
{
  "message": "Hello, John!"
}
```

Personalized greeting with full name:
```json
{
  "message": "Hello, John Doe!"
}
```

**Error Responses:**

**400 Bad Request - Invalid Name Parameter:**

Occurs when the name parameter contains invalid characters or exceeds 100 characters.

```json
{
  "error": "INVALID_NAME",
  "message": "Name parameter contains invalid characters or exceeds 100 characters"
}
```

Example invalid requests:
- `GET /hello?name=John@Doe` (contains special character @)
- `GET /hello?name=John123!` (contains special character !)
- `GET /hello?name=` followed by a string longer than 100 characters

**500 Internal Server Error:**

```json
{
  "error": "INTERNAL_ERROR",
  "message": "Internal server error"
}
```

**cURL Examples:**

```bash
# Basic greeting
curl -X GET "http://localhost:8000/hello"

# Personalized greeting
curl -X GET "http://localhost:8000/hello?name=Alice"

# Greeting with full name
curl -X GET "http://localhost:8000/hello?name=Alice%20Smith"
```

### GET /health

Returns application health status and current timestamp.

**Description:** Health check endpoint that provides the current status of the application along with a UTC timestamp. This endpoint is typically used by monitoring systems and load balancers to verify that the service is running correctly.

**Parameters:** None

**Request Example:**

```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response Schema:**

```json
{
  "status": "string",
  "timestamp": "string"
}
```

**Response Fields:**

| Field | Type | Description | Format |
|-------|------|-------------|---------|
| status | string | Application health status (always "ok") | Fixed value: "ok" |
| timestamp | string | Current UTC timestamp | ISO 8601 format with Z suffix |

**Success Response Example:**

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T14:30:45.123456Z"
}
```

**Error Responses:**

**500 Internal Server Error:**

```json
{
  "error": "INTERNAL_ERROR",
  "message": "Internal server error"
}
```

**cURL Example:**

```bash
curl -X GET "http://localhost:8000/health"
```

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

## Request/Response Examples

### Complete Request/Response Flows

#### Scenario 1: Basic Hello Request

**Request:**
```http
GET /hello HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 26

{
  "message": "Hello, World!"
}
```

#### Scenario 2: Personalized Hello Request

**Request:**
```http
GET /hello?name=Developer HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 29

{
  "message": "Hello, Developer!"
}
```

#### Scenario 3: Invalid Name Parameter

**Request:**
```http
GET /hello?name=User@Domain.com HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**Response:**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
Content-Length: 108

{
  "error": "INVALID_NAME",
  "message": "Name parameter contains invalid characters or exceeds 100 characters"
}
```

#### Scenario 4: Health Check Request

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 65

{
  "status": "ok",
  "timestamp": "2024-01-15T14:30:45.123456Z"
}
```

## Validation Rules

### Name Parameter Validation

The `name` parameter in the `/hello` endpoint is subject to the following validation rules:

1. **Character Set:** Only alphanumeric characters (a-z, A-Z, 0-9) and spaces are allowed
2. **Length:** Maximum 100 characters
3. **Pattern:** Must match regex pattern `^[a-zA-Z0-9 ]+$`
4. **Optional:** Parameter is not required; endpoint works without it

**Valid Examples:**
- `Alice`
- `John Doe`
- `User123`
- `Test User 456`

**Invalid Examples:**
- `user@domain.com` (contains @ symbol)
- `John-Doe` (contains hyphen)
- `User!` (contains exclamation mark)
- `José` (contains accented character)
- A string with 101+ characters

## HTTP Status Codes

| Status Code | Description | When It Occurs |
|-------------|-------------|----------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid name parameter in /hello endpoint |
| 404 | Not Found | Endpoint does not exist |
| 405 | Method Not Allowed | Using wrong HTTP method (e.g., POST on GET endpoint) |
| 422 | Unprocessable Entity | Request validation error |
| 500 | Internal Server Error | Unexpected server error |

## Client Integration Examples

###