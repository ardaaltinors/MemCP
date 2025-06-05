import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.exceptions import ConfigurationError

DATABASE_URL = os.getenv("DB_CONNECTION_URL")

if not DATABASE_URL:
    raise ConfigurationError(
        message="Database connection URL is required",
        config_key="DB_CONNECTION_URL",
        expected_type="string"
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close() 