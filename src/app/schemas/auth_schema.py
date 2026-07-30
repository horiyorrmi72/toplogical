import uuid

from pydantic import BaseModel, EmailStr, Field


class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters long"
    )
    full_name: str = Field(..., min_length=2, max_length=255)


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponseSchema(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True


class UpdateProfileSchema(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)


class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
