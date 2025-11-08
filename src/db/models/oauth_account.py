import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.models.custom_base import CustomBase


class OAuthAccount(CustomBase):
    __tablename__ = "oauth_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    provider = Column(String, nullable=False, index=True)  # e.g., 'google', 'github'
    subject = Column(String, nullable=False, index=True)   # provider user id (sub)
    email = Column(String, nullable=True, index=True)

    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", backref="oauth_accounts")

    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_oauth_provider_subject"),
    )

    def __repr__(self):
        return f"<OAuthAccount(provider='{self.provider}', subject='{self.subject}', user_id={self.user_id})>"

