"""
FastAPI Hello World Application

Main application entry point with CORS middleware, router registration, and startup configuration.
Provides /hello and /health endpoints with proper error handling and validation.

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
from starlette.middleware.cors import CORSMiddleware


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
    
    # Configure CORS middleware
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
        Handle FastAPI validation errors and return formatted 400 response.
        
        Args:
            request: HTTP request object
            exc: Validation error exception
            
        Returns:
            JSONResponse: Formatted error response
        """
        return JSONResponse(
            status_code=400,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Invalid request parameters"
            }
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
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": getattr(exc, 'detail', {}).get('code', 'HTTP_ERROR') if isinstance(exc.detail, dict) else 'HTTP_ERROR',
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            }
        )
    
    @app.exception_handler(Exception)
    async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle unexpected exceptions and return 500 error response.
        
        Args:
            request: HTTP request object
            exc: General exception
            
        Returns:
            JSONResponse: Formatted error response
        """
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        )


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
    
    pattern = r'^[a-zA-Z0-9 ]+$'
    return bool(re.match(pattern, name))


def format_greeting(name: Optional[str]) -> str:
    """
    Format greeting message based on name parameter.
    
    Args:
        name: Optional name for personalization
        
    Returns:
        str: Formatted greeting message
    """
    if not name or not name.strip():
        return "Hello, World!"
    
    return f"Hello, {name.strip()}!"


def get_current_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.
    
    Returns:
        str: Current timestamp in ISO 8601 format with Z suffix
    """
    try:
        return datetime.utcnow().isoformat() + 'Z'
    except Exception:
        # Fallback in case of datetime errors
        return "1970-01-01T00:00:00.000Z"


# Initialize FastAPI application
app = create_app()


@app.get("/hello")
async def get_hello(name: Optional[str] = Query(None, max_length=100)) -> dict[str, str]:
    """
    Process hello request and return greeting message.
    
    Args:
        name: Optional name parameter for personalization (max 100 chars, alphanumeric and spaces only)
        
    Returns:
        dict: JSON response with greeting message
        
    Raises:
        HTTPException: 400 if name contains invalid characters or exceeds length limit
        HTTPException: 500 for internal server errors
    """
    try:
        if name is not None and name.strip():
            if not validate_name(name):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "INVALID_NAME",
                        "message": "Name parameter contains invalid characters or exceeds 100 characters"
                    }
                )
        
        message = format_greeting(name)
        return {"message": message}
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        )


@app.get("/health")
async def get_health() -> dict[str, str]:
    """
    Return health status and current timestamp.
    
    Returns:
        dict: JSON response with status and timestamp
        
    Raises:
        HTTPException: 500 for internal server errors
    """
    try:
        timestamp = get_current_timestamp()
        return {
            "status": "ok",
            "timestamp": timestamp
        }
        
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)