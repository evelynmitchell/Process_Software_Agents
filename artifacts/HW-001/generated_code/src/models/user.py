"""
User SQLAlchemy model with authentication fields, profile data, and relationship to tasks.

This module defines the User model for the application with authentication capabilities,
profile information, and relationships to other entities.

Component ID: COMP-004
Semantic Unit: SU-004

Author: ASP Code Agent
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import re

from src.database.connection import Base


class User(Base):
    """
    User model for authentication and profile management.
    
    This model handles user authentication, profile data, and relationships
    to other entities in the system like tasks.
    
    Attributes:
        id: Primary key identifier
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password for authentication
        first_name: User's first name
        last_name: User's last name
        is_active: Whether the user account is active
        is_verified: Whether the user's email is verified
        bio: Optional user biography
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        last_login: Timestamp of last login
        tasks: Relationship to user's tasks
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamp fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        bio: Optional[str] = None
    ) -> None:
        """
        Initialize a new User instance.
        
        Args:
            username: Unique username (3-50 chars, alphanumeric and underscores)
            email: Valid email address
            password: Plain text password (will be hashed)
            first_name: User's first name (1-100 chars)
            last_name: User's last name (1-100 chars)
            bio: Optional biography (max 1000 chars)
            
        Raises:
            ValueError: If any validation fails
        """
        self.username = self._validate_username(username)
        self.email = self._validate_email(email)
        self.set_password(password)
        self.first_name = self._validate_name(first_name, "first_name")
        self.last_name = self._validate_name(last_name, "last_name")
        self.bio = self._validate_bio(bio) if bio else None
        self.is_active = True
        self.is_verified = False
    
    def __repr__(self) -> str:
        """String representation of User instance."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    @staticmethod
    def _validate_username(username: str) -> str:
        """
        Validate username format and constraints.
        
        Args:
            username: Username to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValueError: If username is invalid
        """
        if not username or not isinstance(username, str):
            raise ValueError("Username is required and must be a string")
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if len(username) > 50:
            raise ValueError("Username must not exceed 50 characters")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        
        return username
    
    @staticmethod
    def _validate_email(email: str) -> str:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            str: Validated email address
            
        Raises:
            ValueError: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise ValueError("Email is required and must be a string")
        
        email = email.strip().lower()
        
        if len(email) > 255:
            raise ValueError("Email must not exceed 255 characters")
        
        # Basic email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email
    
    @staticmethod
    def _validate_name(name: str, field_name: str) -> str:
        """
        Validate first name or last name.
        
        Args:
            name: Name to validate
            field_name: Field name for error messages
            
        Returns:
            str: Validated name
            
        Raises:
            ValueError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"{field_name} is required and must be a string")
        
        name = name.strip()
        
        if len(name) < 1:
            raise ValueError(f"{field_name} cannot be empty")
        
        if len(name) > 100:
            raise ValueError(f"{field_name} must not exceed 100 characters")
        
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValueError(f"{field_name} can only contain letters, spaces, hyphens, and apostrophes")
        
        return name
    
    @staticmethod
    def _validate_bio(bio: str) -> str:
        """
        Validate user biography.
        
        Args:
            bio: Biography to validate
            
        Returns:
            str: Validated biography
            
        Raises:
            ValueError: If bio is invalid
        """
        if not isinstance(bio, str):
            raise ValueError("Bio must be a string")
        
        bio = bio.strip()
        
        if len(bio) > 1000:
            raise ValueError("Bio must not exceed 1000 characters")
        
        return bio if bio else None
    
    def set_password(self, password: str) -> None:
        """
        Set user password with hashing.
        
        Args:
            password: Plain text password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not password or not isinstance(