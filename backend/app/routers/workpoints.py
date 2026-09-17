from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import require_roles
from app.core.timeutils import now_local
from app.models.models import WorkPoint

router = APIRouter(prefix="/api/workpoints", tags=["Work Points"])

DEFAULT_CHECKPOINT_NAME = "КПП ПЧ-13 (Бас проходная)"


class WorkPointCreate(BaseModel):
    name: str
    kind: str = "checkpoint"  # checkpoint | section
    location: Optional[str] = None


class WorkPointUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


def ensure_defaults(db: Session):
    """First-run seed: one checkpoint so QR flow works out of the box."""
    if db.query(WorkPoint).count() == 0:
        db.add(WorkPoint(name=DEFAULT_CHECKPOINT_NAME, kind="checkpoint",
                         location="Бас өткізу орны", is_active=True))
        db.commit()


def to_dict(p: WorkPoint) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "kind": p.kind,
        "location": p.location or "",
        "is_active": p.is_active,
    }


@router.get("")
def list_points(kind: Optional[str] = None, active_only: bool = False,
                db: Session = Depends(get_db)):
    ensure_defaults(db)
    q = db.query(WorkPoint).order_by(WorkPoint.id.asc())
    if kind in ("checkpoint", "section"):
        q = q.filter(WorkPoint.kind == kind)
    if active_only:
        q = q.filter(WorkPoint.is_active == True)  # noqa: E712
    return [to_dict(p) for p in q.all()]


@router.post("")
def create_point(data: WorkPointCreate,
                 db: Session = Depends(get_db),
                 _=Depends(require_roles("DISPATCHER", "BOSS"))):
    name = (data.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Атауы бос болмауы тиіс")
    if data.kind not in ("checkpoint", "section"):
        raise HTTPException(status_code=400, detail="Түрі: checkpoint немесе section")
    p = WorkPoint(name=name, kind=data.kind,
                  location=(data.location or "").strip() or None,
                  is_active=True, created_at=now_local())
    db.add(p)
    db.commit()
    db.refresh(p)
    return to_dict(p)


@router.patch("/{point_id}")
def update_point(point_id: int, data: WorkPointUpdate,
                 db: Session = Depends(get_db),
                 _=Depends(require_roles("DISPATCHER", "BOSS"))):
    p = db.query(WorkPoint).filter(WorkPoint.id == point_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Нүкте табылмады")
    if data.name is not None and data.name.strip():
        p.name = data.name.strip()
    if data.location is not None:
        p.location = data.location.strip() or None
    if data.is_active is not None:
        p.is_active = data.is_active
    db.commit()
    db.refresh(p)
    return to_dict(p)


@router.delete("/{point_id}")
def delete_point(point_id: int,
                 db: Session = Depends(get_db),
                 _=Depends(require_roles("DISPATCHER", "BOSS"))):
    p = db.query(WorkPoint).filter(WorkPoint.id == point_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Нүкте табылмады")
    db.delete(p)
    db.commit()
    return {"status": "SUCCESS"}
