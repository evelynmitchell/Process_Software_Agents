"""
User SQLAlchemy model with authentication fields, profile data, and relationship to tasks.

This module defines the User model for the application with authentication capabilities,
profile information, and relationships to other entities.

Component ID: COMP-004
Semantic Unit: SU-004

Author: ASP Code Generator
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
            ValueError: If username, email, or password validation fails
        """
        self.username = self._validate_username(username)
        self.email = self._validate_email(email)
        self.set_password(password)
        self.first_name = self._validate_name(first_name, "first_name")
        self.last_name = self._validate_name(last_name, "last_name")
        self.bio = bio
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
        if not self._validate_password(password):
            raise ValueError(
                "Password must be at least 8 characters long and contain "
                "at least one uppercase letter, one lowercase letter, and one digit"
            )
        
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
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
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user instance to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive fields like password_hash
            
        Returns:
            dict: User data as dictionary
        """
        user_dict = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.get_full_name(),
            "bio": self.bio,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            user_dict["password_hash"] = self.password_hash
        
        return user_dict
    
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
        
        if len(username) < 3 or len(username) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        
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
            raise ValueError("Email address is too long (maximum