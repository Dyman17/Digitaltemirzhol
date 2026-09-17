from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.core.timeutils import now_local, today_start_local
from app.models.models import ChatMessage, User, Attendance
from app.schemas.schemas import ChatMessageCreate

router = APIRouter(prefix="/api/chat", tags=["Chat"])

def prune_expired_messages(db: Session):
    """Clean up chat messages older than 1 hour to keep DB clean."""
    one_hour_ago = now_local() - timedelta(hours=1)
    deleted = db.query(ChatMessage).filter(ChatMessage.created_at < one_hour_ago).delete()
    if deleted > 0:
        db.commit()

@router.post("/send")
def send_message(
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    token_user=Depends(get_current_user_optional),
):
    prune_expired_messages(db)

    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Хабарлама бос болмауы керек")

    # No guest auto-creation: both sides must be real registered users.
    # When a JWT is present, the sender must be the logged-in user (no impersonation).
    sender_id = token_user.id if token_user is not None else data.sender_id
    sender = db.query(User).filter(User.id == sender_id).first()
    receiver = db.query(User).filter(User.id == data.receiver_id).first()
    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Чат қатысушысы табылмады")

    msg = ChatMessage(
        sender_id=sender.id,
        receiver_id=receiver.id,
        text=data.text.strip(),
        created_at=now_local()
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "sender_name": sender.full_name,
        "sender_role": sender.role,
        "receiver_id": msg.receiver_id,
        "receiver_name": receiver.full_name,
        "text": msg.text,
        "created_at": msg.created_at.strftime("%H:%M:%S")
    }

@router.get("/messages")
def get_messages(
    user1_id: int = Query(...),
    user2_id: int = Query(...),
    db: Session = Depends(get_db)
):
    prune_expired_messages(db)

    messages = db.query(ChatMessage).filter(
        or_(
            and_(ChatMessage.sender_id == user1_id, ChatMessage.receiver_id == user2_id),
            and_(ChatMessage.sender_id == user2_id, ChatMessage.receiver_id == user1_id)
        )
    ).order_by(ChatMessage.created_at.asc()).all()

    results = []
    for m in messages:
        sender_name = m.sender.full_name if m.sender else "Белгісіз"
        receiver_name = m.receiver.full_name if m.receiver else "Белгісіз"
        results.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": sender_name,
            "sender_role": m.sender.role if m.sender else "",
            "receiver_id": m.receiver_id,
            "receiver_name": receiver_name,
            "text": m.text,
            "created_at": m.created_at.strftime("%H:%M:%S")
        })

    return results

@router.get("/users")
def get_chat_users(
    query: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    token_user=Depends(get_current_user_optional),
):
    """Returns users with live presence status for search and chat.

    Privacy: IIN is never exposed here; phone numbers only for logged-in users.
    """
    q = db.query(User)
    if query:
        term = f"%{query.strip()}%"
        q = q.filter(
            or_(
                User.full_name.ilike(term),
                User.username.ilike(term),
                User.position.ilike(term)
            )
        )
    if role:
        q = q.filter(User.role == role)

    users = q.order_by(User.full_name.asc()).all()
    # Same Almaty-wall basis as stored Attendance timestamps
    today_start = today_start_local()

    results = []
    seen_names = set()

    for u in users:
        seen_names.add(u.full_name.lower())
        latest_att = db.query(Attendance).filter(
            Attendance.user_id == u.id,
            Attendance.timestamp >= today_start
        ).order_by(Attendance.timestamp.desc()).first()

        if not latest_att and u.full_name:
            latest_att = db.query(Attendance).filter(
                Attendance.worker_name == u.full_name,
                Attendance.timestamp >= today_start
            ).order_by(Attendance.timestamp.desc()).first()

        is_present = latest_att.action_type == "CHECK_IN" if latest_att else False

        results.append({
            "id": u.id,
            "full_name": u.full_name,
            "role": u.role,
            "position": u.position or "Қызметкер",
            "organization": u.organization or "ПЧ-13 (Алматы дистанциясы)",
            "unit_code": u.unit_code or "ПЧ-13",
            "subdivision": u.subdivision or "Участок №3",
            "emp_num": u.emp_num or f"RG-{u.id:04d}",
            "phone": u.phone if token_user is not None else None,
            "photo_url": u.photo_url or (latest_att.photo_url if latest_att else None),
            "master_id": u.master_id,
            "status": "PRESENT" if is_present else "ABSENT",
            "last_seen": latest_att.timestamp.strftime("%H:%M") if latest_att else None
        })

    # NOTE: unregistered terminal check-ins are intentionally NOT listed here —
    # chat requires a real account. They remain visible in /api/attendance/roster.
    return results
