"""
FastAPI Hello World Application

Main application entry point with CORS middleware, router registration, and startup configuration.
Provides /hello and /health endpoints with comprehensive error handling.

Component ID: COMP-001
Semantic Unit: SU-001

Author: ASP Code Agent
"""

import re
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class HelloResponse(BaseModel):
    """Response model for /hello endpoint."""
    message: str


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    code: str
    message: str


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Hello World API",
        description="Simple REST API with greeting and health check endpoints",
        version="1.0.0",
    )
    
    setup_error_handlers(app)
    return app


def setup_error_handlers(app: FastAPI) -> None:
    """
    Configure global exception handlers for the application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle FastAPI validation errors and return 400 response.
        
        Args:
            request: HTTP request object
            exc: Validation error exception
            
        Returns:
            JSONResponse: 400 error response with INVALID_NAME code
        """
        return JSONResponse(
            status_code=400,
            content={
                "code": "INVALID_NAME",
                "message": "Name parameter contains invalid characters or exceeds 100 characters"
            }
        )
    
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """
        Handle HTTP exceptions and return appropriate error response.
        
        Args:
            request: HTTP request object
            exc: HTTP exception
            
        Returns:
            JSONResponse: Error response with original status and detail
        """
        # Extract error code from detail if it's in the expected format
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=detail
            )
        
        # Default error response format
        code = "INVALID_NAME" if exc.status_code == 400 else "INTERNAL_ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": code,
                "message": detail if isinstance(detail, str) else "An error occurred"
            }
        )
    
    @app.exception_handler(Exception)
    async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle unexpected exceptions and return 500 response.
        
        Args:
            request: HTTP request object
            exc: General exception
            
        Returns:
            JSONResponse: 500 error response with INTERNAL_ERROR code
        """
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        )


def validate_name(name: str) -> bool:
    """
    Validate name parameter contains only alphanumeric characters and spaces.
    
    Args:
        name: Name string to validate
        
    Returns:
        bool: True if name is valid, False otherwise
    """
    if len(name) > 100:
        return False
    
    # Check if name contains only alphanumeric characters and spaces
    pattern = r'^[a-zA-Z0-9\s]*$'
    return bool(re.match(pattern, name))


def sanitize_name(name: str) -> str:
    """
    Clean and format name parameter for safe usage.
    
    Args:
        name: Raw name string
        
    Returns:
        str: Sanitized and formatted name
    """
    # Strip whitespace and title-case the name
    return name.strip().title()


def get_current_timestamp() -> str:
    """
    Generate ISO 8601 formatted UTC timestamp.
    
    Returns:
        str: Current UTC timestamp in ISO 8601 format
    """
    return datetime.utcnow().isoformat() + 'Z'


# Initialize FastAPI application
app = create_app()


@app.get("/hello", response_model=HelloResponse)
async def get_hello(name: Optional[str] = Query(None, max_length=100)) -> HelloResponse:
    """
    Return greeting message, personalized if name provided.
    
    Args:
        name: Optional name parameter for personalization
        
    Returns:
        HelloResponse: JSON response with greeting message
        
    Raises:
        HTTPException: 400 if name parameter is invalid
        
    Example:
        >>> response = await get_hello()
        >>> response.message
        'Hello, World!'
        
        >>> response = await get_hello("John")
        >>> response.message
        'Hello, John!'
    """
    if name is None:
        return HelloResponse(message="Hello, World!")
    
    # Validate name parameter
    if not validate_name(name):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_NAME",
                "message": "Name parameter contains invalid characters or exceeds 100 characters"
            }
        )
    
    # Sanitize and format name
    clean_name = sanitize_name(name)
    
    # Handle empty name after sanitization
    if not clean_name:
        return HelloResponse(message="Hello, World!")
    
    return HelloResponse(message=f"Hello, {clean_name}!")


@app.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """
    Return health status and current UTC timestamp.
    
    Returns:
        HealthResponse: JSON response with status and timestamp
        
    Example:
        >>> response = await get_health()
        >>> response.status
        'ok'
        >>> response.timestamp
        '2023-12-01T10:30:45.123456Z'
    """
    timestamp = get_current_timestamp()
    return HealthResponse(status="ok", timestamp=timestamp)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)