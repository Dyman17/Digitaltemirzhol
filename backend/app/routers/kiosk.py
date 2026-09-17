import hashlib
import hmac
import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import SECRET_KEY, KIOSK_TOKEN_TTL
from app.models.models import Notification

router = APIRouter(prefix="/api/kiosk", tags=["Kiosk & Realtime"])

CHECKPOINT_NAME = "КПП ПЧ-13 (Бас проходная)"


def _token_for_window(window: int) -> str:
    mac = hmac.new(
        SECRET_KEY.encode("utf-8"),
        f"ktz-checkpoint:{window}".encode("utf-8"),
        hashlib.sha256,
    )
    return f"KTZ-{mac.hexdigest()[:12].upper()}"


def current_window() -> int:
    return int(time.time() / KIOSK_TOKEN_TTL)


def is_valid_kiosk_token(token: str) -> bool:
    """Accepts tokens from the current and previous window (clock-skew tolerance)."""
    if not token:
        return False
    token = token.strip().upper()
    w = current_window()
    return token in (_token_for_window(w), _token_for_window(w - 1))


@router.get("/token")
def get_kiosk_qr_token():
    """
    Dynamic QR token for the entrance screen. Rotates every KIOSK_TOKEN_TTL
    seconds — a photographed QR expires, so check-ins must happen on site.
    The check-in page validates it via POST /api/attendance/check-in.
    """
    window = current_window()
    return {
        "token": _token_for_window(window),
        "expires_in": KIOSK_TOKEN_TTL - int(time.time() % KIOSK_TOKEN_TTL),
        "checkpoint_name": CHECKPOINT_NAME,
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
