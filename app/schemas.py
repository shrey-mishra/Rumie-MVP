from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    mode_pref: str
    personality_trait: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    mode_pref: str
    personality_trait: str
    created_at: datetime
    updated_at: Optional[datetime] = None
