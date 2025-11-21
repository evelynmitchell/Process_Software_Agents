"""
Pydantic schemas for authentication request/response validation.

This module defines data validation schemas for authentication endpoints including
login, registration, token management, and user profile operations.

Component ID: COMP-006
Semantic Unit: SU-006

Author: ASP Code Agent
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserRegistrationRequest(BaseModel):
    """Schema for user registration request validation."""
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8-128 characters)",
        example="SecurePassword123!"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User full name",
        example="John Doe"
    )
    
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
        Validate full name contains only allowed characters.
        
        Args:
            v: Full name string to validate
            
        Returns:
            str: Validated and cleaned full name
            
        Raises:
            ValueError: If name contains invalid characters
        """
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v.strip()):
            raise ValueError('Full name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()


class UserLoginRequest(BaseModel):
    """Schema for user login request validation."""
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password",
        example="SecurePassword123!"
    )


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    
    access_token: str = Field(
        ...,
        description="JWT access token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Token type",
        example="bearer"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
        example=3600
    )


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request validation."""
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )


class UserProfile(BaseModel):
    """Schema for user profile information."""
    
    id: int = Field(
        ...,
        description="User unique identifier",
        example=1
    )
    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    full_name: str = Field(
        ...,
        description="User full name",
        example="John Doe"
    )
    is_active: bool = Field(
        default=True,
        description="Whether user account is active",
        example=True
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
        example="2023-01-01T00:00:00Z"
    )
    last_login: Optional[datetime] = Field(
        None,
        description="Last login timestamp",
        example="2023-01-01T12:00:00Z"
    )


class UserRegistrationResponse(BaseModel):
    """Schema for user registration response."""
    
    user: UserProfile = Field(
        ...,
        description="Created user profile information"
    )
    tokens: TokenResponse = Field(
        ...,
        description="Authentication tokens for the new user"
    )


class PasswordChangeRequest(BaseModel):
    """Schema for password change request validation."""
    
    current_password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Current user password",
        example="OldPassword123!"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (8-128 characters)",
        example="NewSecurePassword123!"
    )
    
    @validator('new_password')
    def validate_new_password_strength(cls, v: str) -> str:
        """
        Validate new password meets security requirements.
        
        Args:
            v: New password string to validate
            
        Returns:
            str: Validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('New password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('New password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('New password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('New password must contain at least one special character')
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request validation."""
    
    email: EmailStr = Field(
        ...,
        description="Email address for password reset",
        example="user@example.com"
    )


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation validation."""
    
    token: str = Field(
        ...,
        min_length=1,
        description="Password reset token",
        example="abc123def456"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (8-128 characters)",
        example="NewSecurePassword123!"
    )
    
    @validator('new_password')
    def validate_reset_password_strength(cls, v: str) -> str:
        """
        Validate reset password meets security requirements.
        
        Args:
            v: Reset password string to validate
            
        Returns:
            str: Validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not re.search(r'[A-Z]',