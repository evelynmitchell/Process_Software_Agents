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
            username: Unique username for the user
            email: User's email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            bio: Optional biography text
            
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
            ValueError: If any validation fails
        """
        if first_name is not None:
            self.first_name = self._validate_name(first_name, "first_name")
        if last_name is not None:
            self.last_name = self._validate_name(last_name, "last_name")
        if bio is not None:
            self.bio = self._validate_bio(bio) if bio.strip() else None
    
    @property
    def full_name(self) -> str:
        """
        Get the user's full name.
        
        Returns:
            str: Concatenated first and last name
        """
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """
        Get the user's display name (full name or username).
        
        Returns:
            str: Full name if available, otherwise username
        """
        if self.first_name and self.last_name:
            return self.full_name
        return self.username
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user instance to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive fields like password_hash
            
        Returns:
            dict: User data as dictionary
        """
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "bio": self.bio,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data["password_hash"] = self.password_hash
            
        return data
    
    def _validate_username(self, username: str) -> str:
        """
        Validate username format and length.
        
        Args:
            username: Username to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValueError: If username is invalid