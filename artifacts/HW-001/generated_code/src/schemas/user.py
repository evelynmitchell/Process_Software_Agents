"""
Pydantic schemas for user data validation and serialization.

This module defines all Pydantic models used for user-related operations including
registration, authentication, profile management, and API response formatting.

Component ID: COMP-006
Semantic Unit: SU-006

Author: ASP Code Agent
"""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator, EmailStr


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
        description="Username must be 3-50 characters, alphanumeric and underscores only"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address for account verification"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters with mixed case, numbers, and symbols"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name for profile display"
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
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements.
        
        Password must contain:
        - At least one uppercase letter
        - At least one lowercase letter  
        - At least one digit
        - At least one special character
        
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
            ValueError: If name contains invalid characters
        """
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Full name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip().title()


class UserLoginRequest(BaseModel):
    """
    Schema for user login requests.
    
    Accepts either username or email for authentication along with password.
    """
    username_or_email: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Username or email address for login"
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
        Validate login identifier is either valid username or email format.
        
        Args:
            v: Username or email string to validate
            
        Returns:
            str: Validated identifier
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
                raise ValueError('Username must contain only letters, numbers, and underscores')
        
        return v


class UserProfileUpdateRequest(BaseModel):
    """
    Schema for user profile update requests.
    
    All fields are optional to support partial updates.
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
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="User biography or description"
    )
    
    @validator('full_name')
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize full name if provided.
        
        Args:
            v: Full name string to validate or None
            
        Returns:
            Optional[str]: Sanitized full name or None
            
        Raises:
            ValueError: If name contains invalid characters
        """
        if v is None:
            return v
        
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Full name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip().title()
    
    @validator('bio')
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize bio if provided.
        
        Args:
            v: Bio string to validate or None
            
        Returns:
            Optional[str]: Sanitized bio or None
        """
        if v is None:
            return v
        
        # Remove excessive whitespace and strip
        bio = re.sub(r'\s+', ' ', v.strip())
        return bio if bio else None


class UserPasswordChangeRequest(BaseModel):
    """
    Schema for password change requests.
    
    Requires current password for verification and new password meeting security requirements.
    """
    current_password: str = Field(
        ...,
        description="Current password for verification"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password meeting security requirements"
    )
    confirm_password: str = Field(
        ...,
        description="Confirmation of new password"
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
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at