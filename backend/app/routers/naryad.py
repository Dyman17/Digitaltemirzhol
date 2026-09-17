from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import json

from app.core.database import get_db
from app.core.security import get_current_user_optional, require_roles
from app.core.timeutils import now_local
from app.models.models import Naryad, NaryadBrigade, User, Notification
from app.schemas.schemas import NaryadCreate, NaryadApproveBoss, NaryadPermitDispatcher, NaryadComplete
from app.services.pdf_service import generate_naryad_pdf
from app.services.sign_service import resolve_signature
from app.services import audit as audit_log
from app.core.config import SIGNATURES_DIR, NARYAD_DIR

router = APIRouter(prefix="/api/naryad", tags=["Smart Naryad-Dopusk"])

TECH_CARDS_REFERENCE = [
    {
        "work_type": "Регулировка стыковых зазоров гидравлическими разгонщиками",
        "tech_card_no": "ТК-16 (ҚТЖ-ЦП-2024)",
        "description": "Температуралық режимді ескере отырып, түйіспе саңылауларын нормаға келтіру"
    },
    {
        "work_type": "Смена рельсовых плетей бесстыкового пути",
        "tech_card_no": "ТК-28 (ҚТЖ-ЦП-2023)",
        "description": "Түйіссіз жолдың рельс тізбектерін ауыстыру және кернеуді түсіру"
    },
    {
        "work_type": "Рихтовка и рихтовочно-подбивочные работы на кривых участках",
        "tech_card_no": "ТК-31 (ҚТЖ-ЦП-2024)",
        "description": "Жол осін план бойынша дұрыстау және балласт призмасын тығыздау"
    },
    {
        "work_type": "Одиночная смена стрелочного перевода и рамных рельсов",
        "tech_card_no": "ТК-44 (ҚТЖ-ЦП-2022)",
        "description": "Стрелкалық бағыттаманы және өткірліктерді жекелей ауыстыру"
    },
    {
        "work_type": "Ультразвуковая дефектоскопия рельсов и сварных стыков",
        "tech_card_no": "ТК-09 (ҚТЖ-ЦП-2025)",
        "description": "Дефектоскоп арбасымен рельстердің ішкі жасырын жарықтарын анықтау"
    }
]

SAFETY_MEASURES_DEFAULT = [
    "ДУ-46 журналына бекітілді",
    "Қызыл сигналды қалқандар орнатылды (800 м)",
    "Сигналист ысқырықпен сапқа қойылды",
    "Петардалар және ескерту плакаттары қойылды",
    "Бригада мүшелерімен мақсатты нұсқама (целевой инструктаж) жүргізілді"
]

@router.get("/reference")
def get_references():
    return {
        "tech_cards": TECH_CARDS_REFERENCE,
        "safety_measures": SAFETY_MEASURES_DEFAULT
    }

@router.post("/create")
def create_naryad(
    data: NaryadCreate,
    db: Session = Depends(get_db),
    author=Depends(require_roles("MASTER", "BOSS")),
):
    # The author is the logged-in master (or boss) — no more hardcoded master_id=2.
    master = db.query(User).filter(User.id == author.id).first()

    count = db.query(Naryad).count() + 1
    doc_number = f"№451-2026/{count:02d}"

    naryad = Naryad(
        number=doc_number,
        master_id=master.id,
        organization=data.organization,
        subdivision=data.subdivision,
        work_type=data.work_type,
        tech_card_no=data.tech_card_no,
        location=data.location,
        safety_measures=", ".join(data.safety_measures),
        plan_start=data.plan_start,
        plan_end=data.plan_end,
        status="PENDING_BOSS",
        master_signature_url=resolve_signature(master, "Мастер"),
    )
    db.add(naryad)
    db.commit()
    db.refresh(naryad)

    # Attach brigade members if provided
    if data.brigade_user_ids:
        for uid in data.brigade_user_ids:
            b_item = NaryadBrigade(naryad_id=naryad.id, user_id=uid, briefing_signed=True)
            db.add(b_item)

    # Notify Boss
    notif = Notification(
        target_role="BOSS",
        title="📝 Жаңа Наряд-допуск келді",
        message=f"Жол шебері {master.full_name if master else 'Мастер'} {doc_number} нарядын қол қоюға жолдады.",
        category="NARYAD"
    )
    db.add(notif)
    db.commit()
    audit_log.log_event(db, master, audit_log.NARYAD_CREATE, "naryad", naryad.id,
                        f"{doc_number}: {data.work_type}")

    return {"status": "SUCCESS", "naryad_id": naryad.id, "number": doc_number}

@router.get("/list")
def list_naryads(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Naryad).order_by(Naryad.id.desc())
    if status:
        query = query.filter(Naryad.status == status)
    
    naryads = query.all()
    results = []
    for n in naryads:
        results.append({
            "id": n.id,
            "number": n.number,
            "master_name": n.master.full_name if n.master else "—",
            "boss_name": n.boss.full_name if n.boss else "—",
            "dispatcher_name": n.dispatcher.full_name if n.dispatcher else "—",
            "work_type": n.work_type,
            "tech_card_no": n.tech_card_no,
            "location": n.location,
            "plan_start": n.plan_start,
            "plan_end": n.plan_end,
            "status": n.status,
            "master_signature_url": n.master_signature_url,
            "boss_signature_url": n.boss_signature_url,
            "dispatcher_signature_url": n.dispatcher_signature_url,
            "pdf_path": n.pdf_path,
            "created_at": n.created_at.strftime("%d.%m.%Y %H:%M")
        })
    return results

@router.post("/approve-boss")
def approve_by_boss(
    data: NaryadApproveBoss,
    db: Session = Depends(get_db),
    boss=Depends(require_roles("BOSS")),
):
    naryad = db.query(Naryad).filter(Naryad.id == data.naryad_id).first()
    if not naryad:
        raise HTTPException(status_code=404, detail="Наряд табылмады")
    if naryad.status != "PENDING_BOSS":
        raise HTTPException(status_code=400, detail="Наряд бұл кезеңде емес (уже рассмотрен)")

    naryad.boss_id = boss.id
    naryad.status = "APPROVED_BOSS"
    # The boss's board signature (or facsimile) is stamped on the document
    naryad.boss_signature_url = resolve_signature(boss, "Бастық")

    # Notify Dispatcher
    notif = Notification(
        target_role="DISPATCHER",
        title="📡 Нарядқа терезе (окно) қажет",
        message=f"{naryad.number} Бастық тарапынан бекітілді. Поезд қозғалыс кестесі бойынша рұқсат күтілуде.",
        category="NARYAD"
    )
    db.add(notif)
    db.commit()
    audit_log.log_event(db, boss, audit_log.NARYAD_APPROVE, "naryad", naryad.id,
                        f"{naryad.number} бекітілді")

    return {"status": "SUCCESS", "message": "Бастық нарядқа қол қойды және Диспетчерге жіберілді"}

@router.post("/permit-dispatcher")
def permit_by_dispatcher(
    data: NaryadPermitDispatcher,
    db: Session = Depends(get_db),
    # BOSS is allowed as fallback (dispatcher page is shared with BOSS role)
    disp=Depends(require_roles("DISPATCHER", "BOSS")),
):
    naryad = db.query(Naryad).filter(Naryad.id == data.naryad_id).first()
    if not naryad:
        raise HTTPException(status_code=404, detail="Наряд табылмады")
    if naryad.status != "APPROVED_BOSS":
        raise HTTPException(status_code=400, detail="Алдымен Бастық бекітуі тиіс")

    naryad.dispatcher_id = disp.id
    naryad.status = "PERMITTED_DISPATCHER"
    naryad.dispatcher_signature_url = resolve_signature(disp, "Диспетчер")

    notif = Notification(
        target_role="ALL",
        title="🟢 Жұмысқа рұқсат берілді!",
        message=f"Диспетчер {naryad.number} бойынша технологиялық терезе берді. Бригада жолға шықты.",
        category="NARYAD"
    )
    db.add(notif)
    db.commit()
    audit_log.log_event(db, disp, audit_log.NARYAD_PERMIT, "naryad", naryad.id,
                        f"{naryad.number}: терезе берілді")

    return {"status": "SUCCESS", "message": "Диспетчер рұқсат берді. Технологиялық терезе ашылды."}

@router.post("/complete")
def complete_naryad(
    data: NaryadComplete,
    db: Session = Depends(get_db),
    closer=Depends(require_roles("MASTER", "BOSS")),
):
    naryad = db.query(Naryad).filter(Naryad.id == data.naryad_id).first()
    if not naryad:
        raise HTTPException(status_code=404, detail="Наряд табылмады")
    if naryad.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Наряд әлдеқашан жабылған")

    naryad.status = "COMPLETED"
    naryad.actual_end = data.actual_end_time
    naryad.closed_at = now_local()

    # Generate official signed PDF
    pdf_url = generate_naryad_pdf(naryad, db)
    naryad.pdf_path = pdf_url

    notif = Notification(
        target_role="ALL",
        title="🏁 Жұмыс аяқталды / Жол босатылды",
        message=f"{naryad.number} аяқталды. Ресми №451 сандық бланкісі жасалды.",
        category="NARYAD"
    )
    db.add(notif)
    db.commit()
    audit_log.log_event(db, closer, audit_log.NARYAD_COMPLETE, "naryad", naryad.id,
                        f"{naryad.number} жабылды")

    return {"status": "SUCCESS", "message": "Наряд жабылды, ресми PDF жасалды", "pdf_path": pdf_url}

@router.get("/download/{naryad_id}")
def download_naryad(naryad_id: int, db: Session = Depends(get_db)):
    naryad = db.query(Naryad).filter(Naryad.id == naryad_id).first()
    if not naryad:
        raise HTTPException(status_code=404, detail="Наряд табылмады")
    
    if not naryad.pdf_path:
        naryad.pdf_path = generate_naryad_pdf(naryad, db)
        db.commit()

    filename = Path(naryad.pdf_path).name
    file_path = NARYAD_DIR / filename
    if not file_path.exists():
        generate_naryad_pdf(naryad, db)

    clean_filename = f"naryad_№451_{naryad.id}.pdf"
    return FileResponse(
        path=str(file_path),
        filename=clean_filename,
        media_type="application/pdf"
    )
