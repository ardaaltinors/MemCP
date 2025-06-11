from typing import Optional
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash, verify_password
from src.db.models.user import User
from src.schemas.user import UserCreate, UserUpdate

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()

async def get_user_by_api_key(db: AsyncSession, api_key: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.api_key == api_key))
    return result.scalars().first()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, db_user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True) # Use model_dump for Pydantic v2+
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"] # Remove plain password
        db_user.hashed_password = hashed_password
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    # Try to find user by username first
    user = await get_user_by_username(db, username=username)
    
    # If not found by username, try by email
    if not user:
        user = await get_user_by_email(db, email=username)
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def is_user_active(user: User) -> bool:
    return user.is_active

async def create_api_key(db: AsyncSession, user: User) -> str:
    """Generate a new API key for the user"""
    # Generate a secure random API key
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    # Update user with the new API key
    user.api_key = api_key
    user.api_key_created_at = datetime.now(timezone.utc)
    
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    return api_key

async def revoke_api_key(db: AsyncSession, user: User) -> bool:
    """Revoke the user's API key"""
    if user.api_key:
        user.api_key = None
        user.api_key_created_at = None
        
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return True
    return False

def has_api_key(user: User) -> bool:
    """Check if user has an active API key"""
    return user.api_key is not None 