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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance with middleware and error handlers
    """
    app = FastAPI(
        title="Hello World API",
        description="Simple REST API that returns greeting messages and health status",
        version="1.0.0",
    )
    
    # Add CORS middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup error handlers
    setup_error_handlers(app)
    
    return app


def setup_error_handlers(app: FastAPI) -> None:
    """
    Configure global exception handlers for the application.
    
    Args:
        app: FastAPI application instance to configure
    """
    
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle FastAPI validation errors and return 400 response.
        
        Args:
            request: The incoming request
            exc: The validation error exception
            
        Returns:
            JSONResponse: 400 error response with validation details
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
        Handle HTTPException and return appropriate JSON response.
        
        Args:
            request: The incoming request
            exc: The HTTP exception
            
        Returns:
            JSONResponse: JSON error response with preserved status code
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": "INVALID_NAME" if exc.status_code == 400 else "HTTP_ERROR",
                "message": exc.detail
            }
        )
    
    @app.exception_handler(Exception)
    async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle unexpected exceptions and return 500 response.
        
        Args:
            request: The incoming request
            exc: The general exception
            
        Returns:
            JSONResponse: 500 error response for internal errors
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
        name: The name string to validate
        
    Returns:
        bool: True if name is valid, False otherwise
    """
    if len(name) > 100:
        return False
    
    pattern = r'^[a-zA-Z0-9 ]+$'
    return bool(re.match(pattern, name))


def sanitize_name(name: str) -> str:
    """
    Clean and format name parameter for safe usage.
    
    Args:
        name: The name string to sanitize
        
    Returns:
        str: Cleaned and formatted name
    """
    return name.strip().title()


def get_current_timestamp() -> str:
    """
    Generate ISO 8601 formatted UTC timestamp.
    
    Returns:
        str: Current UTC timestamp in ISO 8601 format with Z suffix
    """
    return datetime.utcnow().isoformat() + 'Z'


# Create application instance
app = create_app()


@app.get("/hello")
async def get_hello(name: Optional[str] = Query(None, max_length=100)) -> dict[str, str]:
    """
    Generate greeting message based on optional name parameter.
    
    Args:
        name: Optional name parameter for personalized greeting
        
    Returns:
        dict[str, str]: JSON response with greeting message
        
    Raises:
        HTTPException: 400 error if name contains invalid characters
        
    Example:
        >>> await get_hello()
        {'message': 'Hello, World!'}
        >>> await get_hello("John")
        {'message': 'Hello, John!'}
    """
    if name is None:
        return {"message": "Hello, World!"}
    
    if not validate_name(name):
        raise HTTPException(
            status_code=400,
            detail="Name parameter contains invalid characters or exceeds 100 characters"
        )
    
    sanitized_name = sanitize_name(name)
    return {"message": f"Hello, {sanitized_name}!"}


@app.get("/health")
async def get_health() -> dict[str, str]:
    """
    Return health status and current UTC timestamp.
    
    Returns:
        dict[str, str]: JSON response with status and timestamp
        
    Example:
        >>> await get_health()
        {'status': 'ok', 'timestamp': '2023-11-21T17:46:28.707525Z'}
    """
    timestamp = get_current_timestamp()
    return {
        "status": "ok",
        "timestamp": timestamp
    }