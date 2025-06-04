from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from src.core import security
from src.crud import crud_user
from src.db.database import get_db
from src.db.models.user import User as DBUser
from src.schemas import user as user_schema, token as token_schema

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

api_key_scheme = HTTPBearer()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = security.decode_token(token)
    if token_data is None or token_data.sub is None:
        raise credentials_exception
    
    user = crud_user.get_user_by_username(db, username=token_data.sub)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_from_api_key(api_key_auth = Depends(api_key_scheme), db: Session = Depends(get_db)) -> DBUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    api_key = api_key_auth.credentials
    
    user = crud_user.get_user_by_api_key(db, api_key=api_key)
    if user is None:
        raise credentials_exception
    
    if not crud_user.is_user_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_active_user(current_user: DBUser = Depends(get_current_user)) -> DBUser:
    if not crud_user.is_user_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=token_schema.Token, tags=["Authentication"])
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Logs in a user and returns an access token.
    """
    user = crud_user.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", response_model=user_schema.User, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user_in: user_schema.UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = crud_user.get_user_by_email(db, email=user_in.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user_by_username = crud_user.get_user_by_username(db, username=user_in.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud_user.create_user(db=db, user_in=user_in)

@router.get("/users/me", response_model=user_schema.User, tags=["Users"])
async def read_users_me(current_user: DBUser = Depends(get_current_active_user)):
    return current_user

# Example of a protected route
@router.get("/users/me/items/", tags=["Users"])
async def read_own_items(current_user: DBUser = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]




#######################
# API Key endpoints


@router.post("/users/me/api-key", response_model=user_schema.ApiKeyResponse, tags=["API Keys"])
async def create_api_key(current_user: DBUser = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Create a new API key for the current user.
    
    This will replace any existing API key for the user.
    Store the returned API key securely as it won't be shown again.
    """
    api_key = crud_user.create_api_key(db, current_user)
    return {
        "api_key": api_key,
        "created_at": current_user.api_key_created_at
    }

@router.get("/users/me/api-key", response_model=user_schema.ApiKeyInfo, tags=["API Keys"])
async def get_api_key_info(current_user: DBUser = Depends(get_current_active_user)):
    """
    Get the current user's API key information including the actual API key.
    
    Returns whether the user has an API key, the actual key value, and when it was created.
    Keep the API key secure and don't expose it unnecessarily.
    """
    return {
        "has_api_key": crud_user.has_api_key(current_user),
        "api_key": current_user.api_key,
        "created_at": current_user.api_key_created_at
    }

@router.delete("/users/me/api-key", tags=["API Keys"])
async def revoke_api_key(current_user: DBUser = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Revoke the current user's API key.
    
    After calling this endpoint, the API key will no longer be valid for authentication.
    """
    success = crud_user.revoke_api_key(db, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="No API key found")
    return {"message": "API key revoked successfully"}

# Example endpoint that can be accessed with API key
@router.get("/users/me/profile", response_model=user_schema.User, tags=["Users"])
async def get_user_profile_with_api_key(current_user: DBUser = Depends(get_current_user_from_api_key)):
    """
    Get user profile using API key authentication.
    
    This endpoint demonstrates API key authentication. 
    Use the Authorization header with 'Bearer <your-api-key>'.
    """
    return current_user 