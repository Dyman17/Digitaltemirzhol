from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional, require_roles
from app.models.models import Leave, User, Notification
from app.schemas.schemas import LeaveCreate, LeaveApprove
from app.services.face_service import save_base64_image
from app.services.sign_service import resolve_signature
from app.services import audit as audit_log
from app.core.config import LEAVES_DIR

router = APIRouter(prefix="/api/leaves", tags=["Leaves & Medical"])

ALLOWED_ROLES = ("WORKER", "MASTER", "DISPATCHER", "BOSS")

@router.post("/create")
def submit_leave(
    data: LeaveCreate,
    db: Session = Depends(get_db),
    token_user=Depends(get_current_user_optional),
):
    # The author is always the logged-in user — no more hardcoded user_id=4.
    if token_user is None:
        raise HTTPException(status_code=401, detail="Өтініш жіберу үшін жүйеге кіріңіз")
    user = db.query(User).filter(User.id == token_user.id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пайдаланушы табылмады")

    if data.start_date > data.end_date:
        raise HTTPException(status_code=400, detail="Басталу күні аяқталу күнінен кеш болмауы тиіс")

    doc_url = None
    if data.document_base64:
        doc_url = save_base64_image(data.document_base64, LEAVES_DIR, prefix=f"leave_{user.username}")

    leave = Leave(
        user_id=user.id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        document_url=doc_url,
        comment=data.comment,
        status="PENDING"
    )
    db.add(leave)

    type_kz = "Больничный (еңбекке жарамсыздық)" if data.leave_type == "SICK_LEAVE" else "Еңбек демалысы (отпуск)"
    notif = Notification(
        target_role="BOSS",
        title="🏥 Жаңа анықтама / өтініш келді",
        message=f"{user.full_name} {type_kz} өтінішін және емхана құжатын жүктеді.",
        category="LEAVE"
    )
    db.add(notif)
    db.commit()
    db.refresh(leave)
    audit_log.log_event(db, user, audit_log.LEAVE_CREATE, "leave", leave.id,
                        f"{data.leave_type}: {data.start_date} — {data.end_date}")

    return {"status": "SUCCESS", "leave_id": leave.id, "message": "Өтініш Бастықтың қарауына жіберілді"}

@router.get("/list")
def list_leaves(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    token_user=Depends(get_current_user_optional),
):
    # Privacy: non-boss users see only their own applications.
    if token_user is not None and token_user.role != "BOSS":
        user_id = token_user.id
    query = db.query(Leave).order_by(Leave.id.desc())
    if user_id:
        query = query.filter(Leave.user_id == user_id)
    
    leaves = query.all()
    results = []
    for l in leaves:
        results.append({
            "id": l.id,
            "user_id": l.user_id,
            "user_name": l.user.full_name if l.user else "—",
            "position": l.user.position if l.user else "—",
            "leave_type": l.leave_type,
            "start_date": l.start_date,
            "end_date": l.end_date,
            "document_url": l.document_url,
            "status": l.status,
            "comment": l.comment,
            "approved_by_name": l.approved_by.full_name if l.approved_by else None,
            "boss_signature_url": l.boss_signature_url,
            "created_at": l.created_at.strftime("%d.%m.%Y")
        })
    return results

@router.post("/approve")
def approve_leave(
    data: LeaveApprove,
    db: Session = Depends(get_db),
    boss=Depends(require_roles("BOSS")),
):
    leave = db.query(Leave).filter(Leave.id == data.leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Өтініш табылмады")
    if data.status not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="Белгісіз мәртебе")

    leave.status = data.status
    leave.approved_by_id = boss.id
    leave.approved_at = datetime.utcnow()
    # The boss's board signature is stamped on approved applications
    if data.status == "APPROVED":
        leave.boss_signature_url = resolve_signature(boss, "Бастық")

    if data.status == "APPROVED":
        notif = Notification(
            user_id=leave.user_id,
            title="✅ Өтініш бекітілді",
            message=f"Сіздің анықтамаңыз Бастық тарапынан бекітілді ({leave.start_date} — {leave.end_date}). Бұл күндер табельде сақталды.",
            category="LEAVE"
        )
    else:
        notif = Notification(
            user_id=leave.user_id,
            title="❌ Өтініш қайтарылды",
            message=f"Сіздің өтінішіңіз ({leave.start_date} — {leave.end_date}) Бастық тарапынан қайтарылды.",
            category="LEAVE"
        )
    db.add(notif)
    db.commit()
    audit_log.log_event(
        db, boss,
        audit_log.LEAVE_APPROVE if data.status == "APPROVED" else audit_log.LEAVE_REJECT,
        "leave", leave.id, f"{leave.start_date} — {leave.end_date}: {data.status}",
    )

    return {"status": "SUCCESS", "message": "Өтініш қаралды: " + data.status}
