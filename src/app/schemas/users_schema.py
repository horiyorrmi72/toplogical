from pydantic import BaseModel, Field


class UpdateProfileSchema(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)


class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
