from pydantic import BaseModel, EmailStr
from datetime import datetime
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

class LoginRequest(BaseModel):
    email:str
    password: str

class ProfileResponse(BaseModel):
    username: str
    email: str
    joined_on: datetime

    class Config:
        from_attributes = True

    
