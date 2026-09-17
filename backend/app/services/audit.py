"""Unified audit journal helper."""
from datetime import datetime
from app.models.models import AuditLog

# Action codes (stable, used by the frontend filter)
AUTH_REGISTER = "AUTH_REGISTER"
AUTH_LOGIN = "AUTH_LOGIN"
AUTH_RESET = "AUTH_RESET"
USER_APPROVE = "USER_APPROVE"
USER_REJECT = "USER_REJECT"
CHECK_IN = "CHECK_IN"
CHECK_OUT = "CHECK_OUT"
NARYAD_CREATE = "NARYAD_CREATE"
NARYAD_APPROVE = "NARYAD_APPROVE"
NARYAD_PERMIT = "NARYAD_PERMIT"
NARYAD_COMPLETE = "NARYAD_COMPLETE"
LEAVE_CREATE = "LEAVE_CREATE"
LEAVE_APPROVE = "LEAVE_APPROVE"
LEAVE_REJECT = "LEAVE_REJECT"


def log_event(db, actor, action: str, entity: str = "", entity_id=None, detail: str = ""):
    """Never breaks the main flow: audit write failures are swallowed with a print."""
    try:
        db.add(AuditLog(
            actor_id=getattr(actor, "id", None),
            actor_name=getattr(actor, "full_name", None) or "Жүйе",
            actor_role=getattr(actor, "role", None),
            action=action,
            entity=entity or None,
            entity_id=entity_id,
            detail=(detail or "")[:255],
            created_at=datetime.utcnow(),
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Audit log warning: {e}")
