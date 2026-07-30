import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.notifications_model import Notification
from app.models.users_model import User
from app.v1.endpoints.auth import get_current_user

router = APIRouter()


class NotificationSchema(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    is_read: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[NotificationSchema])
async def get_user_notifications(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.patch("/{notification_id}/read", status_code=204)
async def mark_as_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notif = (
        await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.is_read = True
    await db.commit()
    return None
