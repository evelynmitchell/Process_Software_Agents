"""
FastAPI Hello World Application

Simple REST API with a single /hello endpoint that returns a greeting message with timestamp.

Component ID: COMP-001
Semantic Unit: SU-001

Author: ASP Code Agent
"""

from datetime import datetime
from typing import Dict
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HelloResponse(BaseModel):
    """Response model for /hello endpoint."""
    message: str
    timestamp: str
    status: str


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    code: str
    message: str


# Initialize FastAPI application
app = FastAPI(
    title="Hello World API",
    description="Simple REST API that returns a Hello World greeting message",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HelloWorldHandler:
    """Handles GET /hello requests and returns Hello World response with timestamp."""
    
    @staticmethod
    def format_response(message: str) -> Dict[str, str]:
        """
        Formats response with message, timestamp, and status.
        
        Args:
            message: The message to include in the response
            
        Returns:
            dict: Formatted response with message, timestamp, and status
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        return {
            "message": message,
            "timestamp": timestamp,
            "status": "success"
        }
    
    @staticmethod
    def get_hello() -> Dict[str, str]:
        """
        Returns Hello World response with current timestamp.
        
        Returns:
            dict: Response containing Hello World message, timestamp, and status
        """
        return HelloWorldHandler.format_response("Hello World")


# Initialize handler
hello_handler = HelloWorldHandler()


@app.get(
    "/hello",
    response_model=HelloResponse,
    responses={
        200: {"description": "Successful response with Hello World message"},
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
def hello() -> HelloResponse:
    """
    Return a Hello World greeting message with timestamp.

    Returns:
        HelloResponse: JSON response with greeting message, timestamp, and status

    Raises:
        HTTPException: 500 status code for internal server errors

    Example:
        >>> response = hello()
        >>> response.message
        'Hello World'
        >>> response.status
        'success'
    """
    try:
        logger.info("Processing GET /hello request")
        response_data = hello_handler.get_hello()
        logger.info("Successfully processed GET /hello request")
        return HelloResponse(**response_data)
    except Exception as e:
        logger.error(f"Error processing /hello request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        )


@app.get("/health")
def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring.

    Returns:
        dict: Status information
    """
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)