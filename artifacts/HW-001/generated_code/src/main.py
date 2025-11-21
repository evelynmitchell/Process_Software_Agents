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
from typing import Optional, Any
import logging

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastAPIApplication:
    """
    FastAPI application factory and configuration manager.
    
    Handles application initialization, middleware setup, and error handler registration.
    """
    
    @staticmethod
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
        FastAPIApplication.setup_error_handlers(app)
        
        return app
    
    @staticmethod
    def setup_error_handlers(app: FastAPI) -> None:
        """
        Configure global exception handlers for the application.
        
        Args:
            app: FastAPI application instance
        """
        error_handler = ErrorHandler()
        
        app.add_exception_handler(RequestValidationError, error_handler.handle_validation_error)
        app.add_exception_handler(HTTPException, error_handler.handle_http_exception)
        app.add_exception_handler(Exception, error_handler.handle_general_exception)


class HelloEndpoint:
    """
    Handler for the /hello endpoint with name parameter validation.
    
    Provides greeting functionality with optional personalization.
    """
    
    NAME_PATTERN = re.compile(r'^[a-zA-Z0-9 ]+$')
    MAX_NAME_LENGTH = 100
    
    @staticmethod
    def get_hello(name: Optional[str] = None) -> dict[str, str]:
        """
        Process hello request and return greeting message.
        
        Args:
            name: Optional name parameter for personalization
            
        Returns:
            dict: Response containing greeting message
            
        Raises:
            HTTPException: If name parameter is invalid
        """
        if name is not None:
            if not HelloEndpoint.validate_name(name):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "code": "INVALID_NAME",
                            "message": "Name parameter contains invalid characters or exceeds 100 characters"
                        }
                    }
                )
        
        message = HelloEndpoint.format_greeting(name)
        return {"message": message}
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """
        Validate name parameter contains only alphanumeric characters and spaces.
        
        Args:
            name: Name string to validate
            
        Returns:
            bool: True if name is valid, False otherwise
        """
        if not name or len(name.strip()) == 0:
            return False
        
        if len(name) > HelloEndpoint.MAX_NAME_LENGTH:
            return False
        
        return bool(HelloEndpoint.NAME_PATTERN.match(name))
    
    @staticmethod
    def format_greeting(name: Optional[str]) -> str:
        """
        Format greeting message based on name parameter.
        
        Args:
            name: Optional name for personalization
            
        Returns:
            str: Formatted greeting message
        """
        if name is None or len(name.strip()) == 0:
            return "Hello, World!"
        
        return f"Hello, {name.strip()}!"


class HealthEndpoint:
    """
    Handler for the /health endpoint providing application status.
    
    Returns health status and current timestamp information.
    """
    
    @staticmethod
    def get_health() -> dict[str, str]:
        """
        Return health status and current timestamp.
        
        Returns:
            dict: Health status and timestamp information
        """
        timestamp = HealthEndpoint.get_current_timestamp()
        return {
            "status": "ok",
            "timestamp": timestamp
        }
    
    @staticmethod
    def get_current_timestamp() -> str:
        """
        Get current UTC timestamp in ISO 8601 format.
        
        Returns:
            str: Current UTC timestamp with 'Z' suffix
        """
        try:
            return datetime.utcnow().isoformat() + 'Z'
        except Exception as e:
            logger.error(f"Error generating timestamp: {e}")
            # Fallback to basic format if isoformat fails
            return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')


class ErrorHandler:
    """
    Centralized error handling and HTTP status code management.
    
    Provides consistent error response formatting across all endpoints.
    """
    
    async def handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle FastAPI validation errors and return formatted 400 response.
        
        Args:
            request: FastAPI request object
            exc: Validation error exception
            
        Returns:
            JSONResponse: Formatted error response
        """
        logger.warning(f"Validation error on {request.url}: {exc}")
        
        error_response = self.format_error_response(
            status_code=400,
            error_code="VALIDATION_ERROR",
            message="Invalid request parameters"
        )
        
        return JSONResponse(
            status_code=400,
            content=error_response
        )
    
    async def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """
        Handle HTTPException and return formatted error response.
        
        Args:
            request: FastAPI request object
            exc: HTTP exception
            
        Returns:
            JSONResponse: Formatted error response
        """
        logger.warning(f"HTTP exception on {request.url}: {exc.status_code} - {exc.detail}")
        
        # If detail is already formatted as our error structure, use it
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        
        # Otherwise format it
        error_response = self.format_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=str(exc.detail) if exc.detail else "HTTP error occurred"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    async def handle_general_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handle unexpected exceptions and return 500 error response.
        
        Args:
            request: FastAPI request object
            exc: General exception
            
        Returns:
            JSONResponse: Formatted 500 error response
        """
        logger.error(f"Unhandled exception on {request.url}: {type(exc).__name__}: {exc}")
        
        error_response = self.format_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Internal server error"
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    
    @staticmethod
    def format_