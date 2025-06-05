from src.db.database import Base, engine

def init_db():
    """Initialize the database by creating all tables."""
    from src.db.models import Memory, UserMessage, User, ProcessedUserProfile
    
    # Create tables
    Base.metadata.create_all(bind=engine) 