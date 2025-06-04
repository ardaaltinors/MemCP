from typing import Optional
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.core.security import get_password_hash, verify_password
from src.db.models.user import User
from src.schemas.user import UserCreate, UserUpdate

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
    return db.query(User).filter(User.api_key == api_key).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True) # Use model_dump for Pydantic v2+
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"] # Remove plain password
        db_user.hashed_password = hashed_password
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def is_user_active(user: User) -> bool:
    return user.is_active

def create_api_key(db: Session, user: User) -> str:
    """Generate a new API key for the user"""
    # Generate a secure random API key
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    # Update user with the new API key
    user.api_key = api_key
    user.api_key_created_at = datetime.now(timezone.utc)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return api_key

def revoke_api_key(db: Session, user: User) -> bool:
    """Revoke the user's API key"""
    if user.api_key:
        user.api_key = None
        user.api_key_created_at = None
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return True
    return False

def has_api_key(user: User) -> bool:
    """Check if user has an active API key"""
    return user.api_key is not None 