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
        Register a new user with email and password.
        
        Args:
            registration_data: User registration information
            
        Returns:
            User: Created user instance
            
        Raises:
            AuthenticationError: If email already exists or validation fails
        """
        try:
            # Validate email format
            if not self._is_valid_email(registration_data.email):
                raise AuthenticationError("Invalid email format")
            
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.email == registration_data.email.lower()
            ).first()
            
            if existing_user:
                raise AuthenticationError("Email already registered")
            
            # Validate password strength
            if not self._is_valid_password(registration_data.password):
                raise AuthenticationError(
                    "Password must be at least 8 characters with uppercase, lowercase, and number"
                )
            
            # Create new user
            hashed_password = hash_password(registration_data.password)
            new_user = User(
                email=registration_data.email.lower().strip(),
                full_name=registration_data.full_name.strip(),
                hashed_password=hashed_password,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            logger.info(f"User registered successfully: {new_user.email}")
            return new_user
            
        except IntegrityError:
            self.db.rollback()
            raise AuthenticationError("Email already registered")
        except Exception as e:
            self.db.rollback()
            logger.error(f"User registration failed: {str(e)}")
            raise AuthenticationError("Registration failed")
    
    def authenticate_user(self, login_data: UserLoginRequest) -> User:
        """
        Authenticate user with email and password.
        
        Args:
            login_data: User login credentials
            
        Returns:
            User: Authenticated user instance
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        try:
            # Find user by email
            user = self.db.query(User).filter(
                User.email == login_data.email.lower()
            ).first()
            
            if not user:
                raise AuthenticationError("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                raise AuthenticationError("Account is deactivated")
            
            # Verify password
            if not verify_password(login_data.password, user.hashed_password):
                raise AuthenticationError("Invalid email or password")
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"User authenticated successfully: {user.email}")
            return user
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise AuthenticationError("Authentication failed")
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User: User instance if found, None otherwise
        """
        try:
            return self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Failed to retrieve user {user_id}: {str(e)}")
            return None
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email format is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_password(self, password: str) -> bool:
        """
        Validate password strength.
        
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
        
        return has_upper and has_lower and has_digit


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Verify and decode token
        if not verify_token(credentials.credentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user from database
        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(int(user_id))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")