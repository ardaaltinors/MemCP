from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CustomBase(Base):
    __abstract__ = True
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)