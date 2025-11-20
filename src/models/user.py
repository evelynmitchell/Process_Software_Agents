"""
User database model with SQLAlchemy ORM

Defines the User model with authentication fields, profile data, and task relationships.
Includes password hashing, email validation, and audit timestamps.

Component ID: COMP-004
Semantic Unit: SU-004

Author: ASP Code Generator
"""

from datetime import datetime
from typing import Optional, List
import re
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base):
    """
    User model for authentication and profile management.
    
    Stores user credentials, profile information, and maintains relationships
    with tasks and other user-related entities.
    
    Attributes:
        id: Primary key identifier
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password for authentication
        first_name: User's first name
        last_name: User's last name
        is_active: Whether the user account is active
        is_verified: Whether the user's email is verified
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
        last_login: Last successful login timestamp
        bio: Optional user biography
        avatar_url: Optional profile picture URL
    """
    
    __tablename__ = 'users'
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, username: str, email: str, password: str, 
                 first_name: str, last_name: str, bio: Optional[str] = None,
                 avatar_url: Optional[str] = None) -> None:
        """
        Initialize a new User instance.
        
        Args:
            username: Unique username for the user
            email: User's email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            bio: Optional biography text
            avatar_url: Optional profile picture URL
            
        Raises:
            ValueError: If username, email, or password validation fails
        """
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.bio = bio
        self.avatar_url = avatar_url
        self.is_active = True
        self.is_verified = False
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password.
        
        Args:
            password: Plain text password to hash and store
            
        Raises:
            ValueError: If password doesn't meet security requirements
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one digit")
        
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
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
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        """Mark the user's email as verified."""
        self.is_verified = True
        self.updated_at = datetime.utcnow()
    
    def update_profile(self, first_name: Optional[str] = None, 
                      last_name: Optional[str] = None,
                      bio: Optional[str] = None,
                      avatar_url: Optional[str] = None) -> None:
        """
        Update user profile information.
        
        Args:
            first_name: New first name (optional)
            last_name: New last name (optional)
            bio: New biography (optional)
            avatar_url: New avatar URL (optional)
        """
        if first_name is not None:
            self.first_name = first_name
        
        if last_name is not None:
            self.last_name = last_name
        
        if bio is not None:
            self.bio = bio
        
        if avatar_url is not None:
            self.avatar_url = avatar_url
        
        self.updated_at = datetime.utcnow()
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (active and verified)."""
        return self.is_active and self.is_verified
    
    @validates('username')
    def validate_username(self, key: str, username: str) -> str:
        """
        Validate username format and requirements.
        
        Args:
            key: Field name being validated
            username: Username value to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValueError: If username validation fails
        """
        if not username:
            raise ValueError("Username cannot be empty")
        
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if len(username) > 50:
            raise ValueError("Username cannot exceed 50 characters")
        
        if not re.match(r'^[a-zA-Z0-9_-]+