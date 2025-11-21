# Hello World API

A simple FastAPI REST API that returns personalized greeting messages with comprehensive error handling and health monitoring.

## Features

- **Personalized Greetings**: `/hello` endpoint with optional name parameter
- **Health Monitoring**: `/health` endpoint with status and timestamp
- **Input Validation**: Secure name parameter validation with alphanumeric and space characters only
- **Error Handling**: Comprehensive JSON error responses with consistent format
- **CORS Support**: Cross-origin requests enabled for development
- **Interactive Documentation**: Auto-generated API docs with Swagger UI and ReDoc

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

### Custom Port

If port 8000 is already in use:

```bash
uvicorn main:app --port 8001
```

## API Documentation

### GET /hello

Returns a personalized greeting message.

**Parameters:**
- `name` (optional, query parameter): Name to include in greeting
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

**Success Response with Name (200 OK):**
```json
{
  "message": "Hello, John Doe!"
}
```

**Error Response - Invalid Name (400 Bad Request):**
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

# Invalid characters (returns 400 error)
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

## Input Validation

The API implements strict input validation for security:

### Name Parameter Rules

- **Maximum length**: 100 characters
- **Allowed characters**: Letters (a-z, A-Z), numbers (0-9), and spaces
- **Automatic formatting**: Names are trimmed and title-cased
- **Invalid examples**: 
  - `Alice@domain.com` (contains @ symbol)
  - `John<script>` (contains < and > symbols)
  - Names longer than 100 characters

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=. --cov-report=html
```

View coverage report by opening `htmlcov/index.html` in your browser.

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_main.py -v

# Integration tests only
pytest tests/test_integration.py -v
```

## Development

### Project Structure

```
.
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── tests/
│   ├── test_main.py    # Unit tests
│   └── test_integration.py  # Integration tests
└── README.md           # This file
```

### Code Quality

The project follows Python best practices:

- **PEP 8**: Python style guide compliance
- **Type hints**: Full type annotation coverage
- **Docstrings**: Comprehensive documentation
- **Error handling**: Robust exception management
- **Input validation**: Security-focused validation
- **Testing**: High test coverage with unit and integration tests

### Adding New Endpoints

1. Define the endpoint function in `main.py`
2. Add appropriate type hints and docstrings
3. Implement input validation if needed
4. Add error handling with consistent JSON responses
5. Write comprehensive tests in `tests/`

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

#### Permission Denied (Production)

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**: Use a port above 1024 or run with appropriate permissions:
```bash
uvicorn main:app --port 8080
```

#### CORS Issues in Browser

**Error**: Cross-origin request blocked

**Solution**: The API includes CORS middleware for development. For production, configure specific origins in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

### Debugging

#### Enable Debug Logging

Add logging configuration to see detailed request information:

```bash
uvicorn main:app --log-level debug
```

#### Test API Endpoints

Use curl or httpie to test endpoints:

```bash
# Test basic functionality
curl -v http://localhost:8000/hello

# Test with parameters
curl -v "http://localhost:8000/hello?name=Test User"

# Test health endpoint
curl -v http://localhost:8000/health
```

#### Validate JSON Responses

Use jq to format JSON responses:

```bash
curl -s http://localhost:8000/hello | jq .
```

### Performance Considerations

- The API is designed for high concurrency with FastAPI's async capabilities
- No blocking operations in endpoint handlers
- Minimal memory footprint with no external dependencies
- Suitable for containerization with Docker

### Security Notes

- Input validation prevents injection attacks
- No sensitive data stored or transmitted
- CORS configured for development (restrict for production)
- Error messages don't expose internal system details
- No authentication required (add as needed for production use)

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write comprehensive tests for new features
4. Update documentation for API changes
5. Ensure all tests pass before submitting changes

## License

This project is provided as-is for educational and development purposes.