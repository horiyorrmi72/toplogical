import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications_model import Notification


class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession, user_id: uuid.UUID, title: str, message: str
    ) -> Notification:
        notif = Notification(user_id=user_id, title=title, message=message)
        db.add(notif)
        return notif
