import uuid # New import
from sqlalchemy import Column, Integer, ForeignKey, Text # Added Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID # New import for UUID
from src.db.models.custom_base import CustomBase

class ProcessedUserProfile(CustomBase):
    __tablename__ = "processed_user_profiles"

    id = Column(Integer, primary_key=True, index=True) # Keeping Integer PK for this table
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True) # Changed to UUID
    metadata_json = Column(JSONB, nullable=True) # Column to store user metadata as JSON
    summary_text = Column(Text, nullable=True) # Added from your previous models.py

    user = relationship("User", back_populates="processed_profile", uselist=False) # Ensured uselist=False for one-to-one

    def __repr__(self):
        return f"<ProcessedUserProfile(id={self.id}, user_id={self.user_id}, updated_at='{self.updated_at}')>" 