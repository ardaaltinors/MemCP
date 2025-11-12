from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, datetime, timezone

from src.core import security
from src.core.config import get_mcp_connection_url
from src.crud import crud_user, crud_server_property
from src.db.database import get_async_db
from src.db.models.user import User as DBUser
from src.schemas import user as user_schema, token as token_schema
from src.core.security import verify_password, get_password_hash
from src.exceptions import (
    InvalidCredentialsError, InactiveUserError, InvalidAPIKeyError,
    DuplicateRecordError, RecordNotFoundError
)
from src.exceptions.handlers import ExceptionHandler
from src.utils.user_cache import invalidate_user_cache

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

api_key_scheme = HTTPBearer()

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)) -> DBUser:
    token_data = security.decode_token(token)
    if token_data is None or token_data.sub is None:
        raise InvalidCredentialsError(message="Could not validate credentials")
    
    user = await crud_user.get_user_by_username(db, username=token_data.sub)
    if user is None:
        raise InvalidCredentialsError(message="User not found", username=token_data.sub)
    return user


async def get_current_user_from_api_key(api_key_auth = Depends(api_key_scheme), db: AsyncSession = Depends(get_async_db)) -> DBUser:
    api_key = api_key_auth.credentials
    
    user = await crud_user.get_user_by_api_key(db, api_key=api_key)
    if user is None:
        raise InvalidAPIKeyError(api_key_prefix=api_key[:10] + "..." if len(api_key) > 10 else api_key)
    
    if not crud_user.is_user_active(user):
        raise InactiveUserError(user_id=str(user.id), username=user.username)
    
    return user


async def get_current_active_user(current_user: DBUser = Depends(get_current_user)) -> DBUser:
    if not crud_user.is_user_active(current_user):
        raise InactiveUserError(user_id=str(current_user.id), username=current_user.username)
    return current_user


async def get_current_active_superuser(current_user: DBUser = Depends(get_current_active_user)) -> DBUser:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

@router.post("/token", response_model=token_schema.Token, tags=["Authentication"])
async def login_for_access_token(db: AsyncSession = Depends(get_async_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Logs in a user and returns an access token.
    """
    user = await crud_user.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise InvalidCredentialsError(username=form_data.username)
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.now(timezone.utc) + access_token_expires
    access_token = security.create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_at": expires_at
    }

@router.post("/users/", response_model=user_schema.User, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user_in: user_schema.UserCreate, db: AsyncSession = Depends(get_async_db)):
    # Check if registration is active
    if not await crud_server_property.is_registration_active(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User registration is currently disabled"
        )
    
    db_user_by_email = await crud_user.get_user_by_email(db, email=user_in.email)
    if db_user_by_email:
        raise DuplicateRecordError(
            message="Email already registered", 
            table_name="users",
            conflicting_field="email",
            conflicting_value=user_in.email
        )
    db_user_by_username = await crud_user.get_user_by_username(db, username=user_in.username)
    if db_user_by_username:
        raise DuplicateRecordError(
            message="Username already registered",
            table_name="users", 
            conflicting_field="username",
            conflicting_value=user_in.username
        )
    return await crud_user.create_user(db=db, user_in=user_in)

@router.get("/users/me", response_model=user_schema.User, tags=["Users"])
async def read_users_me(current_user: DBUser = Depends(get_current_active_user)):
    return current_user


@router.post("/users/me/password", tags=["Users"])
async def change_password(
    password_change: user_schema.PasswordChangeRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Change the current user's password.
    """
    # Verify the old password
    if not verify_password(password_change.old_password, current_user.hashed_password):
        raise InvalidCredentialsError(message="Invalid current password")

    # Update the password
    current_user.hashed_password = get_password_hash(password_change.new_password)
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)

    invalidate_user_cache(current_user)

    return {"message": "Password changed successfully"}




#######################
# API Key endpoints


@router.post("/users/me/api-key", response_model=user_schema.ApiKeyResponse, tags=["API Keys"])
async def create_api_key(current_user: DBUser = Depends(get_current_active_user), db: AsyncSession = Depends(get_async_db)):
    """
    Create a new API key for the current user.
    
    This will replace any existing API key for the user.
    Store the returned API key securely as it won't be shown again.
    """
    api_key = await crud_user.create_api_key(db, current_user)
    return {
        "api_key": api_key,
        "created_at": current_user.api_key_created_at
    }

@router.get("/users/me/api-key", response_model=user_schema.ApiKeyInfo, tags=["API Keys"])
async def get_api_key_info(current_user: DBUser = Depends(get_current_active_user)):
    """
    Get the current user's API key information including the actual API key.
    
    Returns whether the user has an API key, the actual key value, and when it was created.
    """
    has_api_key = crud_user.has_api_key(current_user)
    connection_url = None
    
    if has_api_key and current_user.api_key:
        connection_url = get_mcp_connection_url(current_user.api_key)
    
    return {
        "has_api_key": has_api_key,
        "api_key": current_user.api_key,
        "created_at": current_user.api_key_created_at,
        "connection_url": connection_url
    }

@router.delete("/users/me/api-key", tags=["API Keys"])
async def revoke_api_key(current_user: DBUser = Depends(get_current_active_user), db: AsyncSession = Depends(get_async_db)):
    """
    Revoke the current user's API key.

    After calling this endpoint, the API key will no longer be valid for authentication.
    """
    success = await crud_user.revoke_api_key(db, current_user)
    if not success:
        raise RecordNotFoundError(
            message="No API key found for this user",
            table_name="users",
            record_id=str(current_user.id)
        )
    return {"message": "API key revoked successfully"}


@router.delete("/users/me", tags=["Users"], status_code=status.HTTP_200_OK)
async def delete_account(
    deletion_request: user_schema.AccountDeletionRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Permanently delete user account and ALL associated data.
    """
    REQUIRED_CONFIRMATION = "DELETE"

    if deletion_request.confirm != REQUIRED_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid confirmation string. You must provide exactly: "{REQUIRED_CONFIRMATION}"'
        )

    try:
        stats = await crud_user.delete_user_and_all_data(db, current_user)
        await db.commit()

        return {
            "message": "Account and all associated data have been permanently deleted",
            "deletion_stats": stats
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )