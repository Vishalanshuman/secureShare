from pydantic import BaseModel, EmailStr, Field
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional

# Enum for user roles
class UserRole(str, PyEnum):
    OPS = "OPS"
    CLIENT = "CLIENT"

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)  # Enforce strong passwords

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_verified: bool
    created_at: datetime

    class Config:
        orm_mode = True

class EmailVerificationResponse(BaseModel):
    message: str
    email_verified: bool

class SecureURLResponse(BaseModel):
    download_link: str
    message: str

class Token(BaseModel):
    token_type: str
    access_toke:str
