import time
import hashlib
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Notification

router = APIRouter(prefix="/api/kiosk", tags=["Kiosk & Realtime"])

@router.get("/token")
def get_kiosk_qr_token():
    """
    Generates a dynamic QR token valid for the current 10-second window.
    Prevents screenshot cheating.
    """
    epoch_window = int(time.time() / 10)
    secret = f"ktz_dynamic_qr_salt_{epoch_window}"
    token = hashlib.sha256(secret.encode()).hexdigest()[:16].upper()
    return {
        "token": f"KTZ-CHECKPOINT-{token}",
        "expires_in": 10 - int(time.time() % 10),
        "checkpoint_name": "КПП ПЧ-13 (Бас проходная)"
    }

@router.get("/notifications")
def get_notifications(role: str = "BOSS", db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(
        (Notification.target_role == role) | (Notification.target_role == "ALL")
    ).order_by(Notification.id.desc()).limit(15).all()

    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "category": n.category,
            "created_at": n.created_at.strftime("%H:%M:%S")
        }
        for n in notifs
    ]
