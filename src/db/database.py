from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session with proper cleanup.
    
    This generator ensures the database session is always closed,
    even if an exception occurs during database operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 