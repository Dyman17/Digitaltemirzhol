from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.models import Leave, User, Notification
from app.schemas.schemas import LeaveCreate, LeaveApprove
from app.services.face_service import save_base64_image
from app.core.config import LEAVES_DIR

router = APIRouter(prefix="/api/leaves", tags=["Leaves & Medical"])

@router.post("/create")
def submit_leave(data: LeaveCreate, user_id: int = 4, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = db.query(User).filter(User.role == "WORKER").first()

    doc_url = None
    if data.document_base64:
        doc_url = save_base64_image(data.document_base64, LEAVES_DIR, prefix=f"leave_{user.username if user else 'usr'}")

    leave = Leave(
        user_id=user.id if user else 1,
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
        message=f"{user.full_name if user else 'Жұмыскер'} {type_kz} өтінішін және емхана құжатын жүктеді.",
        category="LEAVE"
    )
    db.add(notif)
    db.commit()
    db.refresh(leave)

    return {"status": "SUCCESS", "leave_id": leave.id, "message": "Өтініш Бастықтың қарауына жіберілді"}

@router.get("/list")
def list_leaves(user_id: Optional[int] = None, db: Session = Depends(get_db)):
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
            "created_at": l.created_at.strftime("%d.%m.%Y")
        })
    return results

@router.post("/approve")
def approve_leave(data: LeaveApprove, db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == data.leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Өтініш табылмады")

    boss = db.query(User).filter(User.role == "BOSS").first()
    leave.status = data.status
    leave.approved_by_id = boss.id if boss else None
    leave.approved_at = datetime.utcnow()

    notif = Notification(
        user_id=leave.user_id,
        title="✅ Өтініш бекітілді",
        message=f"Сіздің анықтамаңыз Бастық тарапынан бекітілді ({leave.start_date} — {leave.end_date}). Бұл күндер табельде сақталды.",
        category="LEAVE"
    )
    db.add(notif)
    db.commit()

    return {"status": "SUCCESS", "message": "Анықтама сәтті бекітілді және годовой графикке енгізілді"}
