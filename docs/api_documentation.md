# Hello World API Documentation

Complete API documentation for the Hello World REST API service.

## Overview

The Hello World API is a simple REST service that provides a single endpoint returning a greeting message with timestamp information. This API demonstrates basic REST principles and JSON response formatting.

**Base URL:** `http://localhost:8000`

**API Version:** 1.0.0

**Content Type:** `application/json`

## Architecture

The API follows a minimal REST architecture with a single component:

- **HelloWorldHandler**: Processes GET requests to `/hello` endpoint
- **Framework**: FastAPI with automatic JSON serialization
- **Server**: Uvicorn ASGI server
- **Language**: Python 3.12

## Authentication

No authentication is required for any endpoints in this API.

## Rate Limiting

No rate limiting is currently implemented.

## Endpoints

### GET /hello

Returns a Hello World greeting message with current timestamp.

**URL:** `/hello`

**Method:** `GET`

**Authentication Required:** No

**Parameters:** None

#### Request

No request body or parameters required.

```bash
curl -X GET "http://localhost:8000/hello"
```

#### Response

**Success Response (200 OK):**

```json
{
  "message": "Hello World",
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "status": "success"
}
```

**Response Schema:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `message` | string | Static greeting message (always "Hello World") | `"Hello World"` |
| `timestamp` | string | ISO 8601 UTC timestamp when response was generated | `"2024-01-15T10:30:45.123456Z"` |
| `status` | string | Response status (always "success" for 200 responses) | `"success"` |

**Response Headers:**

```
Content-Type: application/json
Content-Length: 89
```

#### Error Responses

**Internal Server Error (500):**

```json
{
  "detail": "Internal server error"
}
```

**Error Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `detail` | string | Error description |

#### Status Codes

| Code | Description | When It Occurs |
|------|-------------|----------------|
| `200` | OK | Request processed successfully |
| `500` | Internal Server Error | Unexpected server error during processing |

#### Examples

**Successful Request:**

```bash
# Request
curl -X GET "http://localhost:8000/hello" \
  -H "Accept: application/json"

# Response
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Hello World",
  "timestamp": "2024-01-15T14:22:33.789012Z",
  "status": "success"
}
```

**Using Python requests:**

```python
import requests

response = requests.get("http://localhost:8000/hello")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Output:
# Status: 200
# Response: {'message': 'Hello World', 'timestamp': '2024-01-15T14:22:33.789012Z', 'status': 'success'}
```

**Using JavaScript fetch:**

```javascript
fetch('http://localhost:8000/hello')
  .then(response => response.json())
  .then(data => {
    console.log('Message:', data.message);
    console.log('Timestamp:', data.timestamp);
    console.log('Status:', data.status);
  });
```

### GET /docs

FastAPI automatically generates interactive API documentation.

**URL:** `/docs`

**Method:** `GET`

**Description:** Swagger UI interface for testing API endpoints

**Response:** HTML page with interactive API documentation

### GET /redoc

Alternative API documentation interface.

**URL:** `/redoc`

**Method:** `GET`

**Description:** ReDoc interface for API documentation

**Response:** HTML page with API documentation

### GET /openapi.json

OpenAPI specification in JSON format.

**URL:** `/openapi.json`

**Method:** `GET`

**Description:** Machine-readable API specification

**Response:** JSON OpenAPI 3.0 specification

## Data Types

### Timestamp Format

All timestamps in the API use ISO 8601 format in UTC timezone:

- **Format:** `YYYY-MM-DDTHH:MM:SS.fffffZ`
- **Example:** `2024-01-15T14:22:33.789012Z`
- **Timezone:** Always UTC (indicated by 'Z' suffix)

### String Fields

All string fields use UTF-8 encoding and are returned as JSON strings.

## Error Handling

The API uses standard HTTP status codes and returns error information in JSON format.

### Error Response Format

```json
{
  "detail": "Error description"
}
```

### Common Error Scenarios

| Scenario | Status Code | Response |
|----------|-------------|----------|
| Server exception during processing | 500 | `{"detail": "Internal server error"}` |
| Invalid HTTP method | 405 | `{"detail": "Method Not Allowed"}` |
| Endpoint not found | 404 | `{"detail": "Not Found"}` |

## Performance

### Response Times

- **Target Response Time:** < 10ms
- **Processing Overhead:** Minimal (no database or external API calls)
- **Concurrent Requests:** Supported via ASGI server

### Optimization Notes

- No database queries required
- Static message content
- Minimal timestamp generation overhead
- FastAPI automatic JSON serialization

## Security

### Data Exposure

The API does not expose any sensitive information:

- No server details in responses
- No internal system paths
- No configuration information
- Only specified message, timestamp, and status fields

### Input Validation

No user input is accepted by the `/hello` endpoint, eliminating input validation concerns.

## Testing

### Manual Testing

Test the endpoint using curl:

```bash
# Basic functionality test
curl -X GET "http://localhost:8000/hello"

# Test with verbose output
curl -v -X GET "http://localhost:8000/hello"

# Test response headers
curl -I -X GET "http://localhost:8000/hello"
```

### Automated Testing

Example test cases for the API:

```python
def test_hello_endpoint_success():
    """Test successful hello endpoint response."""
    response = client.get("/hello")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Hello World"
    assert data["status"] == "success"
    assert "timestamp" in data

def test_hello_endpoint_timestamp_format():
    """Test timestamp format is ISO 8601."""
    response = client.get("/hello")
    data = response.json()
    
    # Verify timestamp ends with 'Z' (UTC)
    assert data["timestamp"].endswith("Z")
    
    # Verify timestamp can be parsed
    from datetime import datetime
    datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
```

## Integration

### Client Libraries

The API can be consumed by any HTTP client library:

**Python:**
- `requests`
- `httpx`
- `urllib`

**JavaScript:**
- `fetch` (native)
- `axios`
- `node-fetch`

**Java:**
- `HttpClient`
- `OkHttp`
- `RestTemplate`

### Response Parsing

Example response parsing in different languages:

**Python:**
```python
import requests
response = requests.get("http://localhost:8000/hello")
data = response.json()
message = data["message"]
timestamp = data["timestamp"]
```

**JavaScript:**
```javascript
const response = await fetch("http://localhost:8000/hello");
const data = await response.json();
const message = data.message;
const timestamp = data.timestamp;
```

**Java:**
```java
// Using Jackson ObjectMapper
ObjectMapper mapper = new ObjectMapper();
JsonNode data = mapper.readTree(responseBody);
String message = data.get("message").asText();
String timestamp = data.get("timestamp").asText();
```

## Monitoring

### Health Checks

Use the `/hello`