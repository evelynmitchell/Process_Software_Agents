# Hello World API

A simple FastAPI REST API that returns greeting messages with optional personalization and health monitoring capabilities.

## Features

- **Personalized Greetings**: `/hello` endpoint with optional name parameter
- **Health Monitoring**: `/health` endpoint with status and timestamp
- **Input Validation**: Secure parameter validation and sanitization
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Interactive Documentation**: Auto-generated API docs with Swagger UI and ReDoc
- **Production Ready**: ASGI server support with uvicorn

## Prerequisites

- Python 3.12 or higher
- pip package manager

## Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
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
uvicorn main:app --host 0.0.0.0 --port 8000
```

For production deployment with multiple workers:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

### GET /hello

Returns a greeting message with optional personalization.

**Parameters:**
- `name` (optional, query parameter): Name to personalize greeting
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

**Success Response with name (200 OK):**
```json
{
  "message": "Hello, John Doe!"
}
```

**Error Response (400 Bad Request):**
```json
{
  "code": "INVALID_NAME",
  "message": "Name parameter contains invalid characters or exceeds 100 characters"
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

Returns application health status and current timestamp for monitoring purposes.

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

All endpoints may return the following error response:

**Internal Server Error (500):**
```json
{
  "code": "INTERNAL_ERROR",
  "message": "Internal server error"
}
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
pytest tests/ --cov=. --cov-report=html
```

View coverage report:
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

## Configuration

### Environment Variables

The application supports the following optional environment variables:

```bash
# Server configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Logging level
LOG_LEVEL=info
```

Create a `.env` file in the project root:

```bash
# .env file example
HOST=localhost
PORT=8000
LOG_LEVEL=debug
```

### CORS Configuration

For cross-origin requests, you can enable CORS by modifying the FastAPI application:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Architecture

The application follows a three-layer architecture:

1. **Application Layer** (`FastAPIApplication`): Handles initialization and configuration
2. **Endpoint Layer** (`HelloEndpoint`, `HealthEndpoint`): Implements business logic
3. **Error Handling Layer** (`ErrorHandler`): Provides centralized exception management

### Key Components

- **Input Validation**: Name parameter validation using regex `^[a-zA-Z0-9\s]*$`
- **Sanitization**: Automatic whitespace trimming and title-case formatting
- **Timezone Handling**: All timestamps in UTC using ISO 8601 format
- **Error Consistency**: Standardized error response format with codes and messages

## Security

### Input Validation

- Name parameter limited to 100 characters
- Only alphanumeric characters and spaces allowed
- Automatic sanitization prevents injection attacks
- No direct string interpolation without validation

### Best Practices

- No sensitive data in logs
- Proper HTTP status codes
- Input length restrictions
- Character set validation

## Troubleshooting

### Common Issues

#### Port Already in Use

If port 8000 is already in use:

```bash
# Use a different port
uvicorn main:app --port 8001

# Or find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
```

#### Import Errors

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt

# Or reinstall specific packages
pip install fastapi uvicorn
```

#### Module Not Found

Make sure you're in the correct directory:

```bash
# Should contain main.py
ls -la main.py

# Run from the project root directory
uvicorn main:app --reload
```

#### Permission Errors

On some systems, you might need to use a different port:

```bash
# Use port > 1024 for non-root users
uvicorn main:app --port 8080
```

### Debugging

Enable debug logging:

```bash
# Set log level to debug
uvicorn main:app --log-level debug

# Or use environment variable
LOG_LEVEL=debug uvicorn main:app
```

Check application logs for detailed error information.

### Performance Issues

For high-traffic scenarios:

```bash
# Use multiple workers
uvicorn main:app --workers 4

# Or use gunicorn with uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Health Check Monitoring

Use the `/health` endpoint for monitoring:

```bash
# Simple health check script
while true; do
  curl -f http://localhost:8000/health || echo "Health check failed"
  sleep 30
done
```

## Development

### Code Style

The project follows PEP 8 style guidelines:

- Line length: 88 characters (Black formatter)
- Type hints for all functions
- Docstrings for modules, classes, and functions
- Consistent naming conventions

### Adding New Endpoints

1. Create endpoint function with proper type hints
2. Add input validation and error handling
3. Update API documentation
4. Write comprehensive tests
5. Update this README with new endpoint details

### Contributing

1. Follow existing code style and patterns
2. Add tests for new functionality
3. Update documentation
4. Ensure all tests pass before submitting changes

## License

This project is provided as-is for educational and demonstration purposes.