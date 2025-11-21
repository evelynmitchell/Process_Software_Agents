"""
Authentication API endpoints for user registration, login, token validation, and logout functionality.

This module provides secure authentication endpoints with JWT token management,
password hashing, and comprehensive input validation.

Component ID: COMP-002
Semantic Unit: SU-002

Author: ASP Code Agent
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.user import User
from src.utils.jwt_utils import create_access_token, verify_token, decode_token
from src.utils.password import hash_password, verify_password
from src.schemas.auth import (
    UserRegistrationRequest,
    UserLoginRequest,
    AuthResponse,
    TokenValidationResponse,
    UserResponse,
    LogoutResponse
)
from src.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass


class AuthService:
    """Service class handling authentication business logic."""
    
    def __init__(self, db: Session):
        """
        Initialize authentication service.
        
        Args:
            db: Database session for user operations
        """
        self.db = db
    
    def register_user(self, registration_data: UserRegistrationRequest) -> User:
        """
        Register a new user with validated input data.
        
        Args:
            registration_data: User registration information
            
        Returns:
            User: Created user instance
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            User.email == registration_data.email.lower()
        ).first()
        
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {registration_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "EMAIL_ALREADY_EXISTS",
                        "message": "A user with this email address already exists"
                    }
                }
            )
        
        # Validate password strength
        if not self._validate_password_strength(registration_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "WEAK_PASSWORD",
                        "message": "Password must be at least 8 characters long and contain uppercase, lowercase, number, and special character"
                    }
                }
            )
        
        # Hash password and create user
        hashed_password = hash_password(registration_data.password)
        
        new_user = User(
            email=registration_data.email.lower(),
            username=registration_data.username,
            full_name=registration_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        try:
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            logger.info(f"User registered successfully: {new_user.email}")
            return new_user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database error during user registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "REGISTRATION_FAILED",
                        "message": "Failed to create user account"
                    }
                }
            )
    
    def authenticate_user(self, login_data: UserLoginRequest) -> User:
        """
        Authenticate user with email and password.
        
        Args:
            login_data: User login credentials
            
        Returns:
            User: Authenticated user instance
            
        Raises:
            HTTPException: If credentials are invalid
        """
        user = self.db.query(User).filter(
            User.email == login_data.email.lower()
        ).first()
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password"
                    }
                }
            )
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "ACCOUNT_DISABLED",
                        "message": "User account is disabled"
                    }
                }
            )
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"User authenticated successfully: {user.email}")
        return user
    
    def validate_token(self, token: str) -> User:
        """
        Validate JWT token and return associated user.
        
        Args:
            token: JWT token string
            
        Returns:
            User: User associated with the token
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            if not verify_token(token):
                raise AuthenticationError("Invalid token")
            
            payload = decode_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationError("Token missing user ID")
            
            user = self.db.query(User).filter(User.id == int(user_id)).first()
            
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            return user
            
        except AuthenticationError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid or expired token"
                    }
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "TOKEN_VALIDATION_ERROR",
                        "message": "Failed to validate token"
                    }
                }
            )
    
    def _validate_password_strength(self, password: str) -> bool:
        """
        Validate password meets security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if password meets requirements
        """
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(