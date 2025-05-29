import uuid
from sqlalchemy import Column, DateTime, Text, func, ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.db.database import Base

class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    tags = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Memory(id={self.id}, timestamp='{self.timestamp}', tags='{self.tags}', content='{self.content[:50]}...')>"

class UserMessage(Base):
    __tablename__ = "user_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    message = Column(Text, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<UserMessage(id={self.id}, user_id='{self.user_id}', timestamp='{self.timestamp}', is_processed={self.is_processed}, message='{self.message[:50]}...')>"

class ProcessedUserProfile(Base):
    __tablename__ = "processed_user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)  # Assuming one profile per user for now
    metadata_json = Column(JSONB, nullable=True)
    summary_text = Column(Text, nullable=True)
    last_updated_timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ProcessedUserProfile(id={self.id}, user_id='{self.user_id}', last_updated='{self.last_updated_timestamp}')>" 