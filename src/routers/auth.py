from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from src.core import security
from src.crud import crud_user
from src.db.database import get_db
from src.db.models.user import User as DBUser # Renamed to avoid conflict with schema
from src.schemas import user as user_schema, token as token_schema # Aliased for clarity

router = APIRouter()

# OAuth2PasswordBearer will be used to get the token from the request
# tokenUrl should point to the endpoint that provides the token (our /token endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = security.decode_token(token)
    if token_data is None or token_data.sub is None: # Check if sub is None
        raise credentials_exception
    
    user = crud_user.get_user_by_username(db, username=token_data.sub)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: DBUser = Depends(get_current_user)) -> DBUser:
    if not crud_user.is_user_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=token_schema.Token, tags=["Authentication"])
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
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