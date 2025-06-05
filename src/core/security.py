import os
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import ValidationError

from src.schemas.token import TokenPayload
from src.exceptions import ConfigurationError, InvalidTokenError

# Environment variables
SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES"))

# Raise an error if the environment variables are not set
if not SECRET_KEY:
    raise ConfigurationError(
        message="Authentication secret key is required",
        config_key="AUTH_SECRET_KEY",
        expected_type="string"
    )
if not ACCESS_TOKEN_EXPIRE_MINUTES:
    raise ConfigurationError(
        message="Access token expiration time is required",
        config_key="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
        expected_type="integer"
    )

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hash to verify against
        
    Returns:
        True if the password matches the hash, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The bcrypt hash as a string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')

def decode_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        return token_data
    except (JWTError, ValidationError):
        return None

def decode_token_strict(token: str) -> TokenPayload:
    """
    Decode token with strict error handling - raises exceptions instead of returning None.
    Use this when you want to handle token errors explicitly.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        return token_data
    except JWTError as e:
        raise InvalidTokenError(
            message="Invalid JWT token",
            token_type="JWT",
            validation_error=str(e)
        )
    except ValidationError as e:
        raise InvalidTokenError(
            message="Token payload validation failed",
            token_type="JWT",
            validation_error=str(e)
        ) 