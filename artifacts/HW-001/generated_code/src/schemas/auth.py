"""
Pydantic schemas for authentication request/response validation.

This module defines data validation schemas for authentication endpoints including
login, registration, and token models using Pydantic for request/response validation.

Component ID: COMP-006
Semantic Unit: SU-006

Author: ASP Code Agent
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserRegistrationRequest(BaseModel):
    """
    Schema for user registration request validation.
    
    Validates email format, password strength, and username requirements.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters, alphanumeric and underscores only"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters with at least one uppercase, lowercase, digit, and special character"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Full name, maximum 100 characters"
    )

    @validator('username')
    def validate_username(cls, v: str) -> str:
        """
        Validate username contains only alphanumeric characters and underscores.
        
        Args:
            v: Username string to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValueError: If username contains invalid characters
        """
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v.lower()

    @validator('password')
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets strength requirements.
        
        Args:
            v: Password string to validate
            
        Returns:
            str: Validated password
            
        Raises:
            ValueError: If password doesn't meet strength requirements
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('full_name')
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate full name contains only letters, spaces, hyphens, and apostrophes.
        
        Args:
            v: Full name string to validate
            
        Returns:
            Optional[str]: Validated full name or None
            
        Raises:
            ValueError: If full name contains invalid characters
        """
        if v is not None:
            if not re.match(r"^[a-zA-Z\s\-']+$", v.strip()):
                raise ValueError('Full name must contain only letters, spaces, hyphens, and apostrophes')
            return v.strip()
        return v


class UserLoginRequest(BaseModel):
    """
    Schema for user login request validation.
    
    Validates login credentials using either username or email.
    """
    username_or_email: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Username or email address"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password"
    )

    @validator('username_or_email')
    def validate_username_or_email(cls, v: str) -> str:
        """
        Validate username or email format.
        
        Args:
            v: Username or email string to validate
            
        Returns:
            str: Validated username or email
            
        Raises:
            ValueError: If format is invalid
        """
        v = v.strip().lower()
        
        # Check if it's an email format
        if '@' in v:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        else:
            # Validate as username
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError('Username must contain only alphanumeric characters and underscores')
        
        return v


class TokenResponse(BaseModel):
    """
    Schema for authentication token response.
    
    Contains access token, token type, expiration, and optional refresh token.
    """
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type, typically 'bearer'"
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds"
    )
    refresh_token: Optional[str] = Field(
        None,
        description="JWT refresh token for obtaining new access tokens"
    )
    scope: Optional[str] = Field(
        None,
        description="Token scope permissions"
    )


class TokenRefreshRequest(BaseModel):
    """
    Schema for token refresh request validation.
    
    Validates refresh token format for obtaining new access tokens.
    """
    refresh_token: str = Field(
        ...,
        min_length=10,
        description="Valid refresh token"
    )


class UserResponse(BaseModel):
    """
    Schema for user information response.
    
    Contains safe user data without sensitive information like passwords.
    """
    id: int = Field(
        ...,
        description="Unique user identifier"
    )
    username: str = Field(
        ...,
        description="Username"
    )
    email: str = Field(
        ...,
        description="Email address"
    )
    full_name: Optional[str] = Field(
        None,
        description="Full name"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the user account is active"
    )
    is_verified: bool = Field(
        default=False,
        description="Whether the user email is verified"
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp"
    )
    last_login: Optional[datetime] = Field(
        None,
        description="Last login timestamp"
    )

    class Config:
        """Pydantic configuration for UserResponse."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }


class PasswordChangeRequest(BaseModel):
    """
    Schema for password change request validation.
    
    Validates current password and new password requirements.
    """
    current_password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Current password for verification"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password meeting strength requirements"
    )

    @validator('new_password')
    def validate_new_password_strength(cls, v: str) -> str:
        """
        Validate new password meets strength requirements.
        
        Args:
            v: New password string to validate
            
        Returns:
            str: Validated new password
            
        Raises:
            ValueError: If password doesn't