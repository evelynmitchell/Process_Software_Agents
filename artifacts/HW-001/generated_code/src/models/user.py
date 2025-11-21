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
    to other entities in the system. Includes password hashing, email validation,
    and timestamp tracking.
    
    Attributes:
        id: Primary key identifier
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password for authentication
        first_name: User's first name
        last_name: User's last name
        is_active: Whether the user account is active
        is_verified: Whether the user's email is verified
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        last_login: Timestamp of last successful login
        bio: Optional user biography
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
        bio: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False
    ) -> None:
        """
        Initialize a new User instance.
        
        Args:
            username: Unique username for the user
            email: User's email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            bio: Optional biography text
            is_active: Whether the account is active
            is_verified: Whether the email is verified
            
        Raises:
            ValueError: If validation fails for any field
        """
        self.username = self._validate_username(username)
        self.email = self._validate_email(email)
        self.set_password(password)
        self.first_name = self._validate_name(first_name, "first_name")
        self.last_name = self._validate_name(last_name, "last_name")
        self.bio = self._validate_bio(bio) if bio else None
        self.is_active = is_active
        self.is_verified = is_verified
    
    def set_password(self, password: str) -> None:
        """
        Set the user's password by hashing it.
        
        Args:
            password: Plain text password to hash and store
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        validated_password = self._validate_password(password)
        self.password_hash = generate_password_hash(validated_password)
    
    def check_password(self, password: str) -> bool:
        """
        Check if the provided password matches the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self) -> None:
        """Update the last_login timestamp to current time."""
        self.last_login = datetime.utcnow()
    
    def get_full_name(self) -> str:
        """
        Get the user's full name.
        
        Returns:
            str: Formatted full name (first_name last_name)
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
    
    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
    
    def verify_email(self) -> None:
        """Mark the user's email as verified."""
        self.is_verified = True
    
    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None
    ) -> None:
        """
        Update user profile information.
        
        Args:
            first_name: New first name (optional)
            last_name: New last name (optional)
            bio: New biography (optional)
            
        Raises:
            ValueError: If validation fails for any field
        """
        if first_name is not None:
            self.first_name = self._validate_name(first_name, "first_name")
        if last_name is not None:
            self.last_name = self._validate_name(last_name, "last_name")
        if bio is not None:
            self.bio = self._validate_bio(bio) if bio.strip() else None
    
    @staticmethod
    def _validate_username(username: str) -> str:
        """
        Validate username format and requirements.
        
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
        
        # Allow alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        
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