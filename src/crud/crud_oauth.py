import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.oauth_account import OAuthAccount
from src.db.models.user import User
from src.core.security import get_password_hash


async def get_oauth_account(
    db: AsyncSession, *, provider: str, subject: str
) -> Optional[OAuthAccount]:
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider, OAuthAccount.subject == subject
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, *, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def link_oauth_account(
    db: AsyncSession,
    *,
    user: User,
    provider: str,
    subject: str,
    email: Optional[str],
    access_token: Optional[str],
    refresh_token: Optional[str],
    expires_at: Optional[datetime],
) -> OAuthAccount:
    account = await get_oauth_account(db, provider=provider, subject=subject)
    if account:
        account.email = email or account.email
        account.access_token = access_token
        account.refresh_token = refresh_token
        account.expires_at = expires_at
    else:
        account = OAuthAccount(
            provider=provider,
            subject=subject,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            user_id=user.id,
        )
        db.add(account)
    await db.flush()
    return account


async def get_or_create_user_for_oauth(
    db: AsyncSession,
    *,
    provider: str,
    subject: str,
    email: Optional[str],
    username_hint: Optional[str] = None,
) -> User:
    # If account already linked, return associated user
    account = await get_oauth_account(db, provider=provider, subject=subject)
    if account:
        return account.user

    # Match by email if provided
    if email:
        existing = await get_user_by_email(db, email=email)
        if existing:
            return existing

    # Create a new user
    base_username = (username_hint or (email.split("@")[0] if email else f"{provider}_user")).lower()
    username = base_username
    suffix = 1
    from src.crud.crud_user import get_user_by_username
    while await get_user_by_username(db, username=username):
        suffix += 1
        username = f"{base_username}{suffix}"

    # Generate a random password (not used, but required by schema)
    random_pw_hash = get_password_hash(str(uuid.uuid4()))
    user = User(email=email or f"{username}@{provider}.local", username=username, hashed_password=random_pw_hash)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

