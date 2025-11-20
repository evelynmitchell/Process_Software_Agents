"""
Pydantic schemas for user data validation

This module defines Pydantic models for user-related data validation including
registration, login, authentication, and API response schemas.

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
    Schema for user registration requests.
    
    Validates user input for account creation including email format,
    password strength, and username requirements.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters long"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address required"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters long"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional full name, max 100 characters"
    )

    @validator('username')
    def validate_username(cls, v: str) -> str:
        """
        Validate username format.
        
        Args:
            v: Username string to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValueError: If username contains invalid characters
        """
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()

    @validator('password')
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength requirements.
        
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
        Validate full name format if provided.
        
        Args:
            v: Full name string to validate
            
        Returns:
            Optional[str]: Validated full name or None
            
        Raises:
            ValueError: If full name contains invalid characters
        """
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not re.match(r'^[a-zA-Z\s\'-]+$', v):
                raise ValueError('Full name can only contain letters, spaces, hyphens, and apostrophes')
        return v


class UserLoginRequest(BaseModel):
    """
    Schema for user login requests.
    
    Validates user credentials for authentication.
    """
    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Username or email address"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password"
    )

    @validator('username')
    def validate_username_or_email(cls, v: str) -> str:
        """
        Validate username or email format for login.
        
        Args:
            v: Username or email string to validate
            
        Returns:
            str: Validated username/email
        """
        return v.strip().lower()


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.
    
    Contains safe user information without sensitive data like passwords.
    """
    id: int = Field(..., description="Unique user identifier")
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(True, description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last account update timestamp")

    class Config:
        """Pydantic model configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


class UserUpdateRequest(BaseModel):
    """
    Schema for user profile update requests.
    
    Allows partial updates to user profile information.
    """
    email: Optional[EmailStr] = Field(
        None,
        description="New email address"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated full name"
    )

    @validator('full_name')
    def validate_full_name_update(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate full name format for updates.
        
        Args:
            v: Full name string to validate
            
        Returns:
            Optional[str]: Validated full name or None
            
        Raises:
            ValueError: If full name contains invalid characters
        """
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not re.match(r'^[a-zA-Z\s\'-]+$', v):
                raise ValueError('Full name can only contain letters, spaces, hyphens, and apostrophes')
        return v


class PasswordChangeRequest(BaseModel):
    """
    Schema for password change requests.
    
    Validates current password and new password for security.
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
        description="New password to set"
    )

    @validator('new_password')
    def validate_new_password_strength(cls, v: str) -> str:
        """
        Validate new password strength requirements.
        
        Args:
            v: New password string to validate
            
        Returns:
            str: Validated new password
            
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


class TokenResponse(BaseModel):
    """
    Schema for authentication token responses.
    
    Contains JWT access token and token metadata.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="Authenticated user information")


class UserListResponse(BaseModel):
    """
    Schema for paginated user list responses