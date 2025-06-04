from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from src.db.models.custom_base import CustomBase

class ProcessedUserProfile(CustomBase):
    __tablename__ = "processed_user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    metadata_json = Column(JSONB, nullable=True)
    summary_text = Column(Text, nullable=True)

    user = relationship("User", back_populates="processed_profile", uselist=False)

    def __repr__(self):
        return f"<ProcessedUserProfile(id={self.id}, user_id={self.user_id}, updated_at='{self.updated_at}')>" 