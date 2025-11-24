# Hello World API

A simple FastAPI REST API that returns greeting messages with optional personalization and health status monitoring.

## Features

- **Personalized Greetings**: `/hello` endpoint with optional name parameter
- **Health Monitoring**: `/health` endpoint with status and timestamp
- **Input Validation**: Secure name parameter validation with character restrictions
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Interactive Documentation**: Auto-generated Swagger UI and ReDoc interfaces
- **Type Safety**: Full type hints and Pydantic validation

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

No configuration files are required for basic operation. The API runs with default settings:

- **Host**: localhost (127.0.0.1)
- **Port**: 8000
- **Environment**: development (with auto-reload)

## Running the Application

### Development Mode

Start the development server with auto-reload enabled:

```bash
uvicorn main:app --reload
```

The API will be available at: http://localhost:8000

### Production Mode

Start the production server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Custom Port

To run on a different port:

```bash
uvicorn main:app --port 8001
```

## API Documentation

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Endpoints

#### GET /hello

Returns a greeting message with optional personalization.

**Parameters:**
- `name` (optional, query parameter): Name to personalize the greeting
  - Type: string
  - Max length: 100 characters
  - Allowed characters: alphanumeric and spaces only
  - Pattern: `^[a-zA-Z0-9 ]+$`

**Example Requests:**

```bash
# Basic greeting
curl http://localhost:8000/hello

# Personalized greeting
curl "http://localhost:8000/hello?name=Alice"

# Greeting with spaces in name
curl "http://localhost:8000/hello?name=John%20Doe"
```

**Success Response (200 OK):**

```json
{
  "message": "Hello, World!"
}
```

```json
{
  "message": "Hello, Alice!"
}
```

**Error Responses:**

- **400 Bad Request** - Invalid name parameter:
  ```json
  {
    "error": "INVALID_NAME",
    "message": "Name parameter contains invalid characters or exceeds 100 characters"
  }
  ```

- **500 Internal Server Error** - Server error:
  ```json
  {
    "error": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
  ```

#### GET /health

Returns application health status and current timestamp for monitoring purposes.

**Parameters:** None

**Example Request:**

```bash
curl http://localhost:8000/health
```

**Success Response (200 OK):**

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:45.123456Z"
}
```

**Error Responses:**

- **500 Internal Server Error** - Server error:
  ```json
  {
    "error": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
  ```

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
- **Integration Tests**: Full endpoint testing
- **Validation Tests**: Input parameter validation
- **Error Handling Tests**: Exception and error response testing
- **Edge Case Tests**: Boundary conditions and special inputs

### Example Test Commands

```bash
# Run specific test file
pytest tests/test_main.py -v

# Run tests matching pattern
pytest tests/ -k "test_hello" -v

# Run tests with detailed output
pytest tests/ -v -s
```

## Development

### Project Structure

```
hello-world-api/
├── main.py              # FastAPI application and endpoints
├── requirements.txt     # Python dependencies
├── README.md           # This documentation
└── tests/
    └── test_main.py    # Test suite
```

### Code Quality

The project follows these standards:

- **PEP 8**: Python style guide compliance
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Comprehensive function documentation
- **Error Handling**: Proper exception management
- **Input Validation**: Secure parameter validation

### Adding New Features

1. **Add endpoint logic** to `main.py`
2. **Update API contracts** in docstrings
3. **Add comprehensive tests** in `tests/test_main.py`
4. **Update documentation** in this README
5. **Test thoroughly** before deployment

## Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t hello-world-api .
docker run -p 8000:8000 hello-world-api
```

### Production Considerations

- **Process Manager**: Use Gunicorn with Uvicorn workers
- **Reverse Proxy**: Deploy behind Nginx or similar
- **Environment Variables**: Configure host, port, and other settings
- **Logging**: Implement structured logging for production
- **Monitoring**: Set up health check monitoring
- **Security**: Add HTTPS, rate limiting, and security headers

## Troubleshooting

### Common Issues

#### Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**: Use a different port or kill the process using port 8000

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process (replace PID with actual process ID)
kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8001
```

#### Import Errors

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Install dependencies

```bash
pip install -r requirements.txt
```

#### Permission Errors

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**: Check file permissions or use virtual environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Invalid Name Parameter

**Error**: 400 Bad Request when testing `/hello` endpoint

**Solution**: Ensure name parameter contains only alphanumeric characters and spaces

```bash
# Valid examples
curl "http://localhost:8000/hello?name=Alice"
curl "http://localhost:8000/hello?name=John%20Doe"
curl "http://localhost:8000/hello?name=User123"

# Invalid examples (will return 400 error)
curl "http://localhost:8000/hello?name=user@domain.com"  # Contains @
curl "http://localhost:8000/hello?name=user-name"       # Contains -
```

### Performance Issues

#### Slow Response Times

**Symptoms**: API responses taking longer than expected

**Solutions**:
- Check system resources (CPU, memory)
- Monitor for blocking operations
- Use async/await for I/O operations
- Consider connection pooling for databases

#### High Memory Usage

**