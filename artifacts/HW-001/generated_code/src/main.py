"""
FastAPI Hello World Application

Main application entry point that configures FastAPI with CORS middleware,
error handlers, and endpoint routing for a simple greeting API.

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
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Compile regex for name validation
NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s]*$')


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Hello World API",
        description="Simple REST API that returns greeting messages",
        version="1.0.0"
    )
    
    # Add CORS middleware
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
        app: FastAPI application instance
    """
    
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle FastAPI validation errors and return 400 with proper error format.
        
        Args:
            request: HTTP request object
            exc: Validation error exception
            
        Returns:
            JSONResponse: Formatted error response
        """
        logger.warning(f"Validation error for {request.url}: {exc}")
        return JSONResponse(
            status_code=400,
            content=format_error_response(400, "VALIDATION_ERROR", "Invalid request parameters")
        )
    
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """
        Handle HTTP exceptions and return formatted error response.
        
        Args:
            request: HTTP request object
            exc: HTTP exception
            
        Returns:
            JSONResponse: Formatted error response
        """
        logger.warning(f"HTTP exception for {request.url}: {exc.status_code} - {exc.detail}")
        error_code = getattr(exc, 'error_code', 'HTTP_ERROR')
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(exc.status_code, error_code, exc.detail)
        )
    
    @app.exception_handler(Exception)
    async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle unexpected exceptions and return 500 error.
        
        Args:
            request: HTTP request object
            exc: General exception
            
        Returns:
            JSONResponse: Formatted error response
        """
        logger.error(f"Unexpected error for {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(500, "INTERNAL_ERROR", "Internal server error")
        )


def format_error_response(status_code: int, error_code: str, message: str) -> dict[str, dict[str, str]]:
    """
    Format error response with consistent structure.
    
    Args:
        status_code: HTTP status code
        error_code: Application-specific error code
        message: Error message description
        
    Returns:
        dict: Formatted error response
    """
    return {
        "error": {
            "code": error_code,
            "message": message
        }
    }


def validate_name(name: str) -> bool:
    """
    Validate name parameter contains only alphanumeric characters and spaces.
    
    Args:
        name: Name string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if len(name) > 100:
        return False
    return bool(NAME_PATTERN.match(name))


def sanitize_name(name: str) -> str:
    """
    Clean and format name parameter for safe usage.
    
    Args:
        name: Raw name string
        
    Returns:
        str: Sanitized and formatted name
    """
    return name.strip().title()


def get_current_timestamp() -> str:
    """
    Generate ISO 8601 formatted UTC timestamp.
    
    Returns:
        str: ISO 8601 timestamp with Z suffix
    """
    return datetime.utcnow().isoformat() + 'Z'


# Create FastAPI application
app = create_app()


@app.get("/hello")
async def get_hello(name: Optional[str] = Query(None, max_length=100)) -> dict[str, str]:
    """
    Return greeting message, personalized if name provided.
    
    Args:
        name: Optional name parameter for personalization
        
    Returns:
        dict: JSON response with greeting message
        
    Raises:
        HTTPException: 400 if name contains invalid characters
    """
    if name is not None:
        if not validate_name(name):
            exc = HTTPException(
                status_code=400,
                detail="Name parameter contains invalid characters or exceeds 100 characters"
            )
            exc.error_code = "INVALID_NAME"
            raise exc
        
        sanitized_name = sanitize_name(name)
        if sanitized_name:
            return {"message": f"Hello, {sanitized_name}!"}
    
    return {"message": "Hello, World!"}


@app.get("/health")
async def get_health() -> dict[str, str]:
    """
    Return health status and current UTC timestamp.
    
    Returns:
        dict: JSON response with status and timestamp
    """
    return {
        "status": "ok",
        "timestamp": get_current_timestamp()
    }