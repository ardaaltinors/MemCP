import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: uuid.UUID
    api_key_created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class User(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
    api_key: Optional[str] = None

# Schema for API key responses
class ApiKeyResponse(BaseModel):
    api_key: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ApiKeyInfo(BaseModel):
    has_api_key: bool
    api_key: Optional[str] = None
    created_at: Optional[datetime] = None
    connection_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class ConnectionUrlResponse(BaseModel):
    connection_url: str
    api_key: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

# Schema for processed user profile
class ProcessedUserProfile(BaseModel):
    id: int
    user_id: uuid.UUID
    metadata_json: Optional[dict] = None
    summary_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 