from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import require_roles
from app.models.models import AuditLog
from app.services import audit as audit_log

router = APIRouter(prefix="/api/audit", tags=["Audit Journal"])

ACTION_LABELS = {
    audit_log.AUTH_REGISTER: "Тіркелу",
    audit_log.AUTH_LOGIN: "Кіру",
    audit_log.AUTH_RESET: "Сброс пароля",
    audit_log.USER_APPROVE: "Аккаунт расталды",
    audit_log.USER_REJECT: "Аккаунт қабылданбады",
    audit_log.CHECK_IN: "Жұмысқа келді",
    audit_log.CHECK_OUT: "Жұмыстан кетті",
    audit_log.NARYAD_CREATE: "Наряд құрылды",
    audit_log.NARYAD_APPROVE: "Наряд бекітілді",
    audit_log.NARYAD_PERMIT: "Терезе берілді",
    audit_log.NARYAD_COMPLETE: "Наряд жабылды",
    audit_log.LEAVE_CREATE: "Өтініш жіберілді",
    audit_log.LEAVE_APPROVE: "Өтініш бекітілді",
    audit_log.LEAVE_REJECT: "Өтініш қайтарылды",
}


@router.get("/actions")
def list_actions():
    return [{"code": k, "label": v} for k, v in ACTION_LABELS.items()]


@router.get("/list")
def list_events(
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    boss=Depends(require_roles("BOSS")),
):
    q = db.query(AuditLog).order_by(AuditLog.id.desc())
    if action:
        q = q.filter(AuditLog.action == action)
    events = q.limit(min(max(limit, 1), 500)).all()
    return [
        {
            "id": e.id,
            "actor_name": e.actor_name or "—",
            "actor_role": e.actor_role or "—",
            "action": e.action,
            "action_label": ACTION_LABELS.get(e.action, e.action),
            "entity": e.entity or "—",
            "entity_id": e.entity_id,
            "detail": e.detail or "",
            "created_at": e.created_at.strftime("%d.%m.%Y %H:%M:%S") if e.created_at else "—",
        }
        for e in events
    ]
