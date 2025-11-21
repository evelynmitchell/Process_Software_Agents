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
    """Service class for authentication operations."""
    
    def __init__(self, db: Session):
        """
        Initialize authentication service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def register_user(self, registration_data: UserRegistrationRequest) -> User:
        """
        Register a new user with email and password validation.
        
        Args:
            registration_data: User registration information
            
        Returns:
            User: Created user object
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.email == registration_data.email.lower()
            ).first()
            
            if existing_user:
                logger.warning(f"Registration attempt with existing email: {registration_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = hash_password(registration_data.password)
            
            # Create new user
            new_user = User(
                email=registration_data.email.lower(),
                username=registration_data.username,
                password_hash=hashed_password,
                first_name=registration_data.first_name,
                last_name=registration_data.last_name,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            logger.info(f"User registered successfully: {new_user.email}")
            return new_user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already exists"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    def authenticate_user(self, login_data: UserLoginRequest) -> User:
        """
        Authenticate user with email and password.
        
        Args:
            login_data: User login credentials
            
        Returns:
            User: Authenticated user object
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Find user by email
            user = self.db.query(User).filter(
                User.email == login_data.email.lower()
            ).first()
            
            if not user:
                logger.warning(f"Login attempt with non-existent email: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt with inactive account: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is disabled"
                )
            
            # Verify password
            if not verify_password(login_data.password, user.password_hash):
                logger.warning(f"Failed login attempt for user: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Update last login timestamp
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"User authenticated successfully: {user.email}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Error retrieving user by ID {user_id}: {str(e)}")
            return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
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
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/register", response