from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    model_config = ConfigDict(extra="forbid")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: str


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    role: str = "patient"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[str] = None
