"""
Pydantic schemas for user data validation and serialization.

This module defines all Pydantic models used for user-related operations including
registration, authentication, profile management, and API response serialization.

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
    
    Validates user input for creating new accounts including email format,
    password strength, and username requirements.
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
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name, 1-100 characters"
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
        Validate password meets security requirements.
        
        Args:
            v: Password string to validate
            
        Returns:
            str: Validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
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
    def validate_full_name(cls, v: str) -> str:
        """
        Validate and sanitize full name.
        
        Args:
            v: Full name string to validate
            
        Returns:
            str: Sanitized full name
            
        Raises:
            ValueError: If full name contains invalid characters
        """
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Full name must contain only letters, spaces, hyphens, and apostrophes')
        return v.strip().title()


class UserLoginRequest(BaseModel):
    """
    Schema for user login requests.
    
    Validates user credentials for authentication.
    """
    username: str = Field(
        ...,
        min_length=3,
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
    def normalize_username(cls, v: str) -> str:
        """
        Normalize username for consistent lookup.
        
        Args:
            v: Username string to normalize
            
        Returns:
            str: Normalized username
        """
        return v.lower().strip()


class UserProfileUpdateRequest(BaseModel):
    """
    Schema for user profile update requests.
    
    Allows partial updates to user profile information.
    """
    full_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated full name"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Updated email address"
    )
    
    @validator('full_name')
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize full name if provided.
        
        Args:
            v: Full name string to validate
            
        Returns:
            Optional[str]: Sanitized full name or None
            
        Raises:
            ValueError: If full name contains invalid characters
        """
        if v is None:
            return v
        
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Full name must contain only letters, spaces, hyphens, and apostrophes')
        return v.strip().title()


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
        description="New password meeting security requirements"
    )
    
    @validator('new_password')
    def validate_new_password_strength(cls, v: str) -> str:
        """
        Validate new password meets security requirements.
        
        Args:
            v: New password string to validate
            
        Returns:
            str: Validated new password
            
        Raises:
            ValueError: If password doesn't meet requirements
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


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.
    
    Serializes user information for client consumption, excluding sensitive data.
    """
    id: int = Field(
        ...,
        description="Unique user identifier"
    )
    username: str = Field(
        ...,
        description="User's username"
    )
    email: str = Field(
        ...,
        description="User's email address"
    )
    full_name: str = Field(
        ...,
        description="User's full name"
    )
    is_active: bool = Field(
        ...,
        description="Whether the user account is active"
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        ...,
        description="Last profile update timestamp"
    )
    
    class Config:
        """Pydantic configuration for UserResponse."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }


class UserListResponse(BaseModel):
    """