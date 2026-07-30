from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security_core import get_password_hash, verify_password
from app.db.session import get_db
from app.models.users_model import User
from app.schemas.users_schema import ChangePasswordSchema, UpdateProfileSchema
from app.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.put("/me", response_model=dict)
async def update_profile(
    payload: UpdateProfileSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates user profile details."""
    current_user.full_name = payload.full_name
    await db.commit()
    await db.refresh(current_user)
    return {
        "message": "Profile updated successfully",
        "full_name": current_user.full_name,
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Securely updates the account password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password"
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "Password updated successfully"}
