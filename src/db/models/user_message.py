import uuid
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.models.custom_base import CustomBase

class UserMessage(CustomBase):
    __tablename__ = "user_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=True) # Can be nullable if not all messages belong to a session
    message_content = Column(Text, nullable=False)
    role = Column(String, nullable=False, default="user")  # e.g., "user", "assistant"
    is_processed = Column(Boolean, default=False, nullable=False)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True) # Changed to UUID, made nullable=False
    
    user = relationship("User", back_populates="user_messages")

    def __repr__(self):
        return f"<UserMessage(id={self.id}, user_id={self.user_id}, role='{self.role}', is_processed={self.is_processed}, created_at='{self.created_at}')>" 