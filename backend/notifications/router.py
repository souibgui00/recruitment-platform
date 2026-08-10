import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shared.database import get_db
from user_management.dependencies import get_current_user
from user_management.models import User
from notifications.schemas import NotificationResponse
from notifications.services import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'historique des notifications de l'utilisateur connecté.
    """
    notifications = NotificationService.get_notifications(db, current_user.id)
    return notifications
