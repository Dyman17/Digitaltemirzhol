from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.models.models import ChatMessage, User, Attendance
from app.schemas.schemas import ChatMessageCreate

router = APIRouter(prefix="/api/chat", tags=["Chat"])

def prune_expired_messages(db: Session):
    """Clean up chat messages older than 1 hour to keep DB clean."""
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    deleted = db.query(ChatMessage).filter(ChatMessage.created_at < one_hour_ago).delete()
    if deleted > 0:
        db.commit()

def get_or_create_user(db: Session, user_id: int, fallback_name: str = "Қызметкер") -> User:
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        u = User(
            id=user_id,
            username=f"guest_{user_id}",
            password_hash="system_guest_pass",
            full_name=fallback_name,
            role="WORKER",
            position="Жұмысшы"
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u

@router.post("/send")
def send_message(data: ChatMessageCreate, db: Session = Depends(get_db)):
    prune_expired_messages(db)

    sender = get_or_create_user(db, data.sender_id, "Жөнелтуші")
    receiver = get_or_create_user(db, data.receiver_id, "Алушы")

    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Хабарлама бос болмауы керек")

    msg = ChatMessage(
        sender_id=sender.id,
        receiver_id=receiver.id,
        text=data.text.strip(),
        created_at=datetime.utcnow()
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
    db: Session = Depends(get_db)
):
    """Returns users with live presence status for search and chat."""
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
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

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
            "iin": u.iin or "—",
            "emp_num": u.emp_num or f"RG-{u.id:04d}",
            "photo_url": u.photo_url or (latest_att.photo_url if latest_att else None),
            "master_id": u.master_id,
            "status": "PRESENT" if is_present else "ABSENT",
            "last_seen": latest_att.timestamp.strftime("%H:%M") if latest_att else None
        })

    # Also include unregistered workers from today's attendance (e.g. checked in via camera)
    if not role or role == "WORKER":
        atts_q = db.query(Attendance).filter(Attendance.user_id.is_(None))
        if query:
            atts_q = atts_q.filter(Attendance.worker_name.ilike(f"%{query.strip()}%"))
        unreg_atts = atts_q.order_by(Attendance.timestamp.desc()).all()

        for att in unreg_atts:
            name = (att.worker_name or "").strip()
            if name and name.lower() not in seen_names:
                seen_names.add(name.lower())
                # Ensure they have a user entry in database for chat foreign keys
                existing_u = db.query(User).filter(User.full_name == name).first()
                if not existing_u:
                    existing_u = User(
                        username=f"kpp_{att.id}",
                        password_hash="temp_hash",
                        full_name=name,
                        role="WORKER",
                        position="Жұмысшы (КПП)",
                        emp_num=f"КПП-{att.id:03d}",
                        photo_url=att.photo_url
                    )
                    db.add(existing_u)
                    db.commit()
                    db.refresh(existing_u)

                results.append({
                    "id": existing_u.id,
                    "full_name": existing_u.full_name,
                    "role": "WORKER",
                    "position": existing_u.position,
                    "emp_num": existing_u.emp_num,
                    "photo_url": att.photo_url or existing_u.photo_url,
                    "master_id": None,
                    "status": "PRESENT" if att.action_type == "CHECK_IN" else "ABSENT",
                    "last_seen": att.timestamp.strftime("%H:%M")
                })

    return results
