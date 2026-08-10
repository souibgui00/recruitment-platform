import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from notifications.models import Notification, NotificationType

class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        user_id: uuid.UUID,
        type: NotificationType,
        message: str,
        related_application_id: Optional[uuid.UUID] = None
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            message=message,
            related_application_id=related_application_id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_notifications(db: Session, user_id: uuid.UUID) -> List[Notification]:
        return db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
