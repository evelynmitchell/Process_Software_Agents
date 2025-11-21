# Hello World API

A simple FastAPI REST API that returns greeting messages with optional personalization and health monitoring capabilities.

## Features

- **Personalized Greetings**: `/hello` endpoint with optional name parameter
- **Health Monitoring**: `/health` endpoint with status and timestamp
- **Input Validation**: Secure name parameter validation with length and character restrictions
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Interactive Documentation**: Automatic OpenAPI/Swagger documentation
- **Production Ready**: Proper logging, error handling, and CORS support

## Prerequisites

- Python 3.12 or higher
- pip package manager

## Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

No additional configuration is required for basic usage. The application runs with default settings suitable for development and production.

### Environment Variables (Optional)

You can customize the application behavior using these environment variables:

- `HOST`: Server host address (default: `127.0.0.1`)
- `PORT`: Server port number (default: `8000`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

Create a `.env` file in the project root:
```bash
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
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

If you have Docker installed:

```bash
# Build the image
docker build -t hello-world-api .

# Run the container
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

Health check endpoint that returns application status and current timestamp.

**Success Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:45.123456Z"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

### Error Responses

All endpoints may return these error responses:

**500 Internal Server Error:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
}
```

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

These interfaces allow you to:
- View all available endpoints
- Test API calls directly in the browser
- See request/response schemas
- Download the OpenAPI specification

## Testing

### Running Tests

Run the complete test suite:

```bash
pytest tests/ -v
```

Run tests with coverage report:

```bash
pytest tests/ --cov=. --cov-report=html
```

View the coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Test Categories

The test suite includes:

- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing
- **Edge Case Tests**: Boundary conditions and invalid inputs
- **Error Handling Tests**: Exception scenarios

### Manual Testing

Test the endpoints manually:

```bash
# Test basic hello endpoint
curl -X GET http://localhost:8000/hello

# Test personalized greeting
curl -X GET "http://localhost:8000/hello?name=TestUser"

# Test health endpoint
curl -X GET http://localhost:8000/health

# Test invalid name parameter
curl -X GET "http://localhost:8000/hello?name=Invalid@Name"
```

## Security Considerations

### Input Validation

- **Name Parameter**: Restricted to alphanumeric characters and spaces only
- **Length Limits**: Maximum 100 characters for name parameter
- **Sanitization**: Input is automatically trimmed and formatted

### Error Handling

- **No Information Leakage**: Error responses don't expose internal details
- **Consistent Format**: All errors follow the same JSON structure
- **Proper HTTP Status Codes**: Appropriate status codes for different error types

### Best Practices Implemented

- Input validation using regex patterns
- Parameterized responses (no string injection)
- Proper HTTP status codes
- Comprehensive error handling
- Request/response logging

## Monitoring and Logging

### Health Checks

Use the `/health` endpoint for:
- Load balancer health checks
- Container orchestration health probes
- Monitoring system status checks

### Logging

The application logs:
- Request information (INFO level)
- Validation errors (WARNING level)
- Internal errors (ERROR level)

Log format includes timestamp, level, and message details.

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

#### Invalid Name Parameter

**Error**: 400 Bad Request with INVALID_NAME code

**Solution**: Ensure name parameter:
- Contains only letters, numbers, and spaces
- Is 100 characters or less
- Example: `name=John Doe` ✓, `name=John@Doe` ✗

### Performance Issues

#### Slow Response Times

1. **Check system resources**: CPU and memory usage
2. **Monitor logs**: Look for error patterns
3. **Use production server**: Run with multiple workers:
   ```bash
   uvicorn main:app --workers 4
   ```

#### High Memory Usage

1. **Update dependencies**: Ensure latest versions
2. **Monitor for memory leaks**: Use memory profiling tools
3. **Restart application**: Temporary solution for memory issues

### Debugging

#### Enable Debug Mode

For development debugging:
```bash
uvicorn main:app --reload --log-level debug
```

#### Check Application Logs

View detailed request/response information in the console output.

#### Validate API Responses

Use the interactive documentation at `/docs` to test endpoints and validate responses.

## Development

### Project Structure

```
hello-world-api/
├── main.py              # FastAPI application and endpoints
├── requirements.txt     # Python dependencies
├── tests/              # Test files
│   ├── __init__.py
│   ├── test_main.py    # Unit and integration tests
│   └── conftest.py     # Test configuration
├── README