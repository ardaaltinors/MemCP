from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime

class TokenPayload(BaseModel):
    sub: Optional[str] = None