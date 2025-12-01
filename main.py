#!/usr/bin/env python3
"""
Hello World FastAPI Application.

A simple REST API that provides a single endpoint returning
a Hello World greeting with timestamp.

Author: ASP Code Agent
Date: 2025-11-19
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, Any
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Hello World API",
    description="A simple API that returns Hello World greeting with timestamp",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


class HelloWorldHandler:
    """
    Handles GET /hello requests and returns Hello World response with timestamp.

    This component is responsible for processing hello world requests and
    formatting responses with proper structure including message, timestamp,
    and status fields.
    """

    def get_hello(self) -> Dict[str, str]:
        """
        Returns Hello World response with current timestamp.

        Returns:
            dict[str, str]: Response dictionary containing message, timestamp, and status

        Raises:
            Exception: If timestamp generation fails
        """
        try:
            logger.info("Processing hello world request")
            response = self.format_response("Hello World")
            logger.info(f"Successfully generated hello response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error generating hello response: {str(e)}")
            raise

    def format_response(self, message: str) -> Dict[str, str]:
        """
        Formats response with message, timestamp, and status.

        Args:
            message (str): The message to include in response

        Returns:
            dict[str, str]: Formatted response dictionary

        Raises:
            Exception: If timestamp formatting fails
        """
        try:
            # Generate UTC timestamp in ISO 8601 format
            timestamp = datetime.utcnow().isoformat() + "Z"

            response = {"message": message, "timestamp": timestamp, "status": "success"}

            logger.debug(f"Formatted response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            raise Exception(f"Failed to format response: {str(e)}")


# Initialize handler
hello_handler = HelloWorldHandler()


@app.get("/hello")
async def hello_endpoint() -> Dict[str, str]:
    """
    Returns a simple Hello World greeting message.

    Returns a JSON response containing:
    - message: "Hello World"
    - timestamp: Current UTC timestamp in ISO 8601 format
    - status: "success"

    Returns:
        dict[str, str]: Hello World response with timestamp

    Raises:
        HTTPException: 500 status code for internal server errors
    """
    try:
        logger.info("Received GET request to /hello endpoint")
        response = hello_handler.get_hello()
        logger.info("Successfully processed hello request")
        return response

    except Exception as e:
        logger.error(f"Internal server error in hello endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Internal server error"},
        )


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint providing API information.

    Returns:
        dict[str, str]: API information
    """
    return {
        "message": "Hello World API",
        "version": "1.0.0",
        "endpoints": "/hello",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        dict[str, str]: Health status
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Hello World API server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
