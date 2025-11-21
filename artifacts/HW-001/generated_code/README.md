# Hello World API

A simple FastAPI REST API that returns greeting messages with optional personalization and health monitoring capabilities.

## Features

- **Personalized Greetings**: `/hello` endpoint with optional name parameter
- **Health Monitoring**: `/health` endpoint with status and timestamp
- **Input Validation**: Secure name parameter validation with length and character restrictions
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Auto Documentation**: FastAPI automatic OpenAPI documentation
- **Production Ready**: Proper logging, exception handling, and security practices

## Prerequisites

- Python 3.12 or higher
- pip package manager

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd hello-world-api
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

No configuration files are required for basic operation. The application uses sensible defaults:

- **Host**: 127.0.0.1 (localhost)
- **Port**: 8000
- **Log Level**: INFO
- **Timezone**: UTC

### Environment Variables (Optional)

You can customize the application behavior using environment variables:

```bash
# Server configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Application settings
APP_TITLE="Hello World API"
APP_VERSION="1.0.0"
```

## Running the Application

### Development Mode

Start the development server with auto-reload:

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### Production Mode

Start the production server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker (Optional)

If you have a Dockerfile:

```bash
docker build -t hello-world-api .
docker run -p 8000:8000 hello-world-api
```

## API Documentation

### GET /hello

Returns a greeting message with optional personalization.

**Parameters:**
- `name` (optional, query parameter): Name to personalize the greeting
  - Type: string
  - Max length: 100 characters
  - Allowed characters: alphanumeric and spaces only
  - Example: `?name=John Doe`

**Success Response (200 OK):**
```json
{
  "message": "Hello, World!"
}
```

**Personalized Response (200 OK):**
```json
{
  "message": "Hello, John Doe!"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": {
    "code": "INVALID_NAME",
    "message": "Name parameter contains invalid characters or exceeds 100 characters"
  }
}
```

**Examples:**
```bash
# Basic greeting
curl http://localhost:8000/hello

# Personalized greeting
curl "http://localhost:8000/hello?name=Alice"

# Invalid name (contains special characters)
curl "http://localhost:8000/hello?name=Alice@123"
```

### GET /health

Health check endpoint for monitoring and load balancer health checks.

**Parameters:** None

**Success Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:45.123456Z"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
}
```

**Examples:**
```bash
# Health check
curl http://localhost:8000/health
```

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Testing

### Running Tests

Run the complete test suite:

```bash
pytest tests/ -v
```

Run tests with coverage report:

```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

View HTML coverage report:

```bash
open htmlcov/index.html  # On macOS
# or
start htmlcov/index.html  # On Windows
```

### Test Categories

- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test API endpoints end-to-end
- **Validation Tests**: Test input validation and error handling
- **Edge Case Tests**: Test boundary conditions and error scenarios

### Manual Testing

Test the API manually using curl or any HTTP client:

```bash
# Test basic hello endpoint
curl -X GET "http://localhost:8000/hello" -H "accept: application/json"

# Test personalized greeting
curl -X GET "http://localhost:8000/hello?name=TestUser" -H "accept: application/json"

# Test health endpoint
curl -X GET "http://localhost:8000/health" -H "accept: application/json"

# Test error handling (invalid name)
curl -X GET "http://localhost:8000/hello?name=Invalid@Name!" -H "accept: application/json"
```

## Security Considerations

### Input Validation

- **Name Parameter**: Restricted to alphanumeric characters and spaces only
- **Length Limits**: Maximum 100 characters for name parameter
- **Regex Validation**: Uses `^[a-zA-Z0-9 ]+$` pattern to prevent injection attacks

### Error Handling

- **No Information Disclosure**: Error messages don't expose internal system details
- **Consistent Error Format**: All errors follow the same JSON structure
- **Proper HTTP Status Codes**: 400 for client errors, 500 for server errors

### Best Practices

- **No Sensitive Data**: No authentication tokens or sensitive information in logs
- **Input Sanitization**: All user inputs are validated before processing
- **Exception Handling**: Unhandled exceptions are caught and logged securely

## Monitoring and Logging

### Health Checks

Use the `/health` endpoint for:
- Load balancer health checks
- Container orchestration health probes
- Monitoring system status checks

### Logging

The application logs important events:
- Request processing errors
- Validation failures
- Unhandled exceptions
- Application startup/shutdown

Log levels:
- **INFO**: Normal operation events
- **WARNING**: Validation errors and client mistakes
- **ERROR**: Server errors and exceptions

## Troubleshooting

### Common Issues

#### Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**: Use a different port:
```bash
uvicorn main:app --port 8001
```

#### Import Errors

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

#### Permission Denied (Port 80/443)

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**: Use a port above 1024 or run with sudo (not recommended):
```bash
uvicorn main:app --port 8080
```

#### Virtual Environment Issues

**Error**: Dependencies not found despite installation

**Solution**: Ensure virtual environment is activated:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip list  # Verify packages are installed
```

### Performance Issues

#### Slow Response Times

1. Check system resources (CPU, memory)
2. Verify no blocking operations in endpoints
3. Consider using multiple workers:
   ```bash
   uvicorn main:app --workers 4
   ```

#### High Memory Usage

1. Monitor for memory leaks
2. Check log file sizes
3. Restart the application periodically if needed

### Debugging

#### Enable Debug Mode

For development debugging:
```bash
uvicorn main:app --reload --log-level debug
```

#### Check Application Logs

Monitor application output for errors:
```bash
uvicorn main:app 2>&1 | tee app.log
```

#### Validate API Responses