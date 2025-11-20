# Hello World API

A simple FastAPI REST API that returns a "Hello World" greeting message with timestamp.

## Features

- Single `/hello` endpoint that returns JSON greeting with timestamp
- FastAPI automatic documentation at `/docs` and `/redoc`
- Lightweight and fast ASGI-based server
- ISO 8601 UTC timestamp formatting
- Comprehensive error handling

## Prerequisites

- Python 3.12 or higher
- pip package manager

## Installation

1. Clone or download the project files

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

No configuration is required for this simple API. The application runs with default settings.

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

### Custom Port

To run on a different port:

```bash
uvicorn main:app --port 8001
```

## API Documentation

### GET /hello

Returns a Hello World greeting message with current timestamp.

**URL:** `/hello`

**Method:** `GET`

**Authentication:** None required

**Request Parameters:** None

**Response Format:**

```json
{
  "message": "Hello World",
  "timestamp": "2023-12-07T10:30:45.123456Z",
  "status": "success"
}
```

**Response Fields:**
- `message` (string): Always returns "Hello World"
- `timestamp` (string): Current UTC timestamp in ISO 8601 format
- `status` (string): Always returns "success" for successful requests

**Status Codes:**
- `200 OK`: Success - greeting returned successfully
- `500 Internal Server Error`: Server error occurred

**Example Request:**
```bash
curl -X GET "http://localhost:8000/hello"
```

**Example Response:**
```json
{
  "message": "Hello World",
  "timestamp": "2023-12-07T15:42:33.789012Z",
  "status": "success"
}
```

### Error Responses

When an internal server error occurs:

**Status Code:** `500 Internal Server Error`

**Response Format:**
```json
{
  "code": "INTERNAL_ERROR",
  "message": "Internal server error"
}
```

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These interfaces allow you to:
- View all available endpoints
- Test API calls directly from the browser
- See request/response schemas
- Download OpenAPI specification

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
open htmlcov/index.html
```

### Test Coverage

The test suite includes:
- Unit tests for the HelloWorldHandler component
- Integration tests for the /hello endpoint
- Error handling tests
- Response format validation tests
- Timestamp format validation tests

### Manual Testing

Test the endpoint manually using curl:

```bash
# Test successful response
curl -X GET "http://localhost:8000/hello"

# Test with verbose output to see headers
curl -v -X GET "http://localhost:8000/hello"
```

## Architecture

### Component Overview

- **HelloWorldHandler**: Core component that processes GET requests to /hello endpoint
  - Generates Hello World message
  - Creates ISO 8601 UTC timestamp
  - Formats consistent JSON response
  - Handles exceptions and returns appropriate error responses

### Technology Stack

- **Language:** Python 3.12
- **Web Framework:** FastAPI 0.104+
- **HTTP Server:** Uvicorn ASGI server
- **Datetime Handling:** Python datetime module (stdlib)
- **JSON Serialization:** FastAPI automatic JSON response

### Design Principles

- **Simplicity:** Minimal architecture with single endpoint
- **Consistency:** Standardized response format
- **Reliability:** Comprehensive error handling
- **Performance:** Lightweight with minimal processing overhead
- **Standards Compliance:** ISO 8601 timestamps, REST conventions

## Development

### Code Structure

```
.
├── main.py              # FastAPI application and HelloWorldHandler
├── tests/
│   └── test_main.py     # Unit and integration tests
├── requirements.txt     # Python dependencies
└── README.md           # This documentation
```

### Adding Features

To extend the API:

1. Add new endpoint handlers to `main.py`
2. Create corresponding tests in `tests/`
3. Update this README with new endpoint documentation
4. Update requirements.txt if new dependencies are needed

## Troubleshooting

### Common Issues

#### Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:** Use a different port:
```bash
uvicorn main:app --port 8001
```

Or find and stop the process using port 8000:
```bash
lsof -ti:8000 | xargs kill -9
```

#### Import Errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

#### Python Version Issues

**Error:** `SyntaxError` or compatibility issues

**Solution:** Ensure Python 3.12+ is installed:
```bash
python --version
```

If using an older version, upgrade Python or use pyenv:
```bash
pyenv install 3.12.0
pyenv local 3.12.0
```

#### Permission Denied (Port 80/443)

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solution:** Use a port above 1024 or run with sudo (not recommended):
```bash
uvicorn main:app --port 8000
```

#### Tests Failing

**Error:** Test failures or import errors in tests

**Solution:** 
1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests from project root directory:
   ```bash
   pytest tests/ -v
   ```

3. Check Python path if imports fail:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   pytest tests/ -v
   ```

### Performance Issues

#### Slow Response Times

If responses are slower than expected:

1. Check system resources:
   ```bash
   top
   ```

2. Use production ASGI server settings:
   ```bash
   uvicorn main:app --workers 4
   ```

3. Monitor response times:
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/hello"
   ```

### Debugging

#### Enable Debug Logging

Add logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Check Application Health

The API doesn't include a dedicated health endpoint, but you can verify it's running:

```bash
curl -f http://localhost:8000/hello || echo "API is down"
```

## Support

For issues or questions:

1. Check this troubleshooting section
2. Review the interactive API documentation at `/docs`
3. Run the test suite to verify functionality
4. Check application logs for error details

## License

This is a simple demonstration API. Use and modify as needed for your projects.