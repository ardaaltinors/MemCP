import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.models.custom_base import CustomBase

class User(CustomBase):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Relationship to memories
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    
    # Relationship to user messages
    user_messages = relationship("UserMessage", back_populates="user", cascade="all, delete-orphan")
    
    # Relationship to processed user profile (one-to-one)
    processed_profile = relationship("ProcessedUserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    # Add other relationships here if needed in the future