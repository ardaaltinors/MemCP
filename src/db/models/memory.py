import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.db.models.custom_base import CustomBase

class Memory(CustomBase):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    content = Column(Text, nullable=False)
    tags = Column(JSONB, nullable=True)
    
    # Foreign key to User table
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    user = relationship("User", back_populates="memories")

    def __repr__(self):
        return f"<Memory(id={self.id}, user_id={self.user_id}, created_at='{self.created_at}', tags='{self.tags}', content='{self.content[:30]}...')>" 