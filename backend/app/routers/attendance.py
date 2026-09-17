from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.models import Attendance, User, Notification, Leave
from app.schemas.schemas import AttendanceCheckIn
from app.services.excel_service import generate_timesheet_csv
from app.routers.kiosk import is_valid_kiosk_token, CHECKPOINT_NAME
from app.services import audit as audit_log

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

import base64
import uuid
from app.core.config import ATTENDANCE_DIR

@router.post("/check-in")
def record_attendance(
    data: AttendanceCheckIn,
    db: Session = Depends(get_db),
    token_user=Depends(get_current_user_optional),
):
    if data.action_type not in ("CHECK_IN", "CHECK_OUT"):
        raise HTTPException(status_code=400, detail="Белгісіз әрекет түрі")

    # 1. Resolve worker identity.
    # Logged-in users are identified by their JWT — client-supplied user_id/name
    # is ignored, so nobody can check in as somebody else.
    user = None
    verified_identity = False
    if token_user is not None:
        user = db.query(User).filter(User.id == token_user.id).first()
        verified_identity = user is not None
    if user is None and data.user_id:
        user = db.query(User).filter(User.id == data.user_id).first()

    raw_name = (data.worker_name or "").strip()
    if user is None and raw_name:
        user = db.query(User).filter(User.full_name.ilike(f"%{raw_name}%")).first()

    final_name = user.full_name if user else (raw_name if raw_name else "Қызметкер")
    final_pos = user.position if user else "Жұмысшы"

    # 2. Validate the dynamic QR token when provided (entrance-screen flow).
    qr_ok = is_valid_kiosk_token(data.kiosk_token or "")
    if data.kiosk_token and not qr_ok:
        raise HTTPException(
            status_code=400,
            detail="QR-код ескірген: кіреберістегі экрандағы жаңа кодты сканерлеңіз",
        )

    # 3. Save captured photo to the attendance archive (not the face registry)
    raw_photo = data.photo_base64 or data.face_image_base64
    photo_url = user.photo_url if user else None

    if raw_photo:
        try:
            if "," in raw_photo:
                raw_photo = raw_photo.split(",", 1)[1]
            img_bytes = base64.b64decode(raw_photo)
            if len(img_bytes) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Фото тым үлкен (макс. 5 МБ)")
            filename = f"att_{uuid.uuid4().hex[:12]}.jpg"
            file_path = ATTENDANCE_DIR / filename
            with open(file_path, "wb") as f:
                f.write(img_bytes)
            photo_url = f"/storage/attendance/{filename}"
        except HTTPException:
            raise
        except Exception as e:
            print(f"Photo save error: {e}")

    now = datetime.now()
    action_kz = "жұмысқа келді" if data.action_type == "CHECK_IN" else "жұмыстан кетті"
    time_str = now.strftime("%H:%M")

    if verified_identity:
        note = "JWT-пен расталған тұлға" + (" + QR расталды" if qr_ok else "")
    elif qr_ok:
        note = "QR-экран арқылы (терминал), тұлға расталмаған"
    else:
        note = "Қолмен енгізілген (тұлға мен QR расталмаған)"

    # 4. Save attendance record directly into database
    record = Attendance(
        user_id=user.id if user else None,
        worker_name=final_name,
        photo_url=photo_url,
        action_type=data.action_type,
        timestamp=now,
        checkpoint=data.checkpoint or CHECKPOINT_NAME,
        note=note
    )
    db.add(record)

    # 5. Boss notification
    notif = Notification(
        target_role="BOSS",
        user_id=user.id if user else None,
        title="📸 Өткізу бекетінен фото-фиксация",
        message=f"{final_name} ({final_pos}) сағат {time_str}-де {action_kz}.",
        category="ATTENDANCE",
        created_at=now
    )
    db.add(notif)
    db.commit()
    db.refresh(record)
    audit_log.log_event(
        db, user,
        audit_log.CHECK_IN if data.action_type == "CHECK_IN" else audit_log.CHECK_OUT,
        "attendance", record.id, f"{final_name}: {action_kz} ({time_str})",
    )

    return {
        "status": "SUCCESS",
        "record_id": record.id,
        "action_type": data.action_type,
        "action_text": f"Сәтті тіркелді: {action_kz.capitalize()}",
        "timestamp": now.strftime("%d.%m.%Y %H:%M:%S"),
        "worker_name": final_name,
        "photo_url": photo_url,
        "verified_identity": verified_identity,
        "qr_verified": qr_ok,
        "user": {
            "id": user.id if user else None,
            "full_name": final_name,
            "position": final_pos,
            "emp_num": user.emp_num if user else "—",
            "photo_url": photo_url
        }
    }

@router.get("/recent")
def get_recent_attendance(limit: int = 20, db: Session = Depends(get_db)):
    records = db.query(Attendance).order_by(Attendance.timestamp.desc()).limit(limit).all()
    result = []
    for r in records:
        u = r.user
        result.append({
            "id": r.id,
            "user_id": u.id if u else None,
            "full_name": (u.full_name if u else r.worker_name) or "Қызметкер",
            "position": (u.position if u else "Жұмысшы"),
            "emp_num": (u.emp_num if u else "—"),
            "photo_url": r.photo_url or (u.photo_url if u else None),
            "action_type": r.action_type,
            "timestamp": r.timestamp.strftime("%d.%m.%Y %H:%M:%S"),
            "checkpoint": r.checkpoint
        })
    return result

@router.get("/timesheet")
def get_timesheet(target_date: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Timesheet grouped by workers for ONE calendar day.
    target_date format: YYYY-MM-DD (defaults to today). First CHECK_IN and last
    CHECK_OUT of that day are used; worked hours are computed, not hardcoded.
    """
    from datetime import time as dtime

    users = db.query(User).filter(User.role.in_(["WORKER", "MASTER"])).all()

    selected_date_str = target_date or date.today().strftime("%Y-%m-%d")
    try:
        selected = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Күн форматы: YYYY-MM-DD")
    day_start = datetime.combine(selected, dtime.min)
    day_end = datetime.combine(selected, dtime.max)

    def fmt_hours(delta) -> str:
        total_min = int(delta.total_seconds() // 60)
        return f"{total_min // 60} сағат {total_min % 60:02d} мин"

    results = []
    for u in users:
        # Check leaves for this user on this date
        leave = db.query(Leave).filter(
            Leave.user_id == u.id,
            Leave.status == "APPROVED",
            Leave.start_date <= selected_date_str,
            Leave.end_date >= selected_date_str
        ).first()

        leave_status = None
        if leave:
            if leave.leave_type == "SICK_LEAVE":
                leave_status = "БОЛЬНИЧНЫЙ (Еңбекке жарамсыз)"
            elif leave.leave_type == "VACATION":
                leave_status = "ОТПУСК (Еңбек демалысы)"
            else:
                leave_status = "ДЕКРЕТ / ДЕМАЛЫС"

        # Attendance of THIS day only (by id or by exact full-name match)
        day_filter = [
            Attendance.timestamp >= day_start,
            Attendance.timestamp <= day_end,
        ]
        att_in = db.query(Attendance).filter(
            Attendance.action_type == "CHECK_IN",
            (Attendance.user_id == u.id) | (Attendance.worker_name == u.full_name),
            *day_filter
        ).order_by(Attendance.timestamp.asc()).first()

        att_out = db.query(Attendance).filter(
            Attendance.action_type == "CHECK_OUT",
            (Attendance.user_id == u.id) | (Attendance.worker_name == u.full_name),
            *day_filter
        ).order_by(Attendance.timestamp.desc()).first()

        check_in_str = att_in.timestamp.strftime("%H:%M") if att_in else "—"
        check_out_str = att_out.timestamp.strftime("%H:%M") if att_out else "—"

        if att_in and att_out and att_out.timestamp > att_in.timestamp:
            hours_str = fmt_hours(att_out.timestamp - att_in.timestamp)
        elif att_in:
            hours_str = "Жұмыста"
        else:
            hours_str = "—"
        status_badge = leave_status if leave_status else ("Жұмыста" if att_in else "Келмеген")

        results.append({
            "user_id": u.id,
            "emp_num": u.emp_num or f"RG-{u.id:04d}",
            "full_name": u.full_name,
            "position": u.position or "Монтер пути",
            "date": selected_date_str,
            "check_in": check_in_str,
            "check_out": check_out_str,
            "hours": hours_str,
            "status": status_badge,
            "leave_type": leave.leave_type if leave else None
        })

    return {
        "selected_date": selected_date_str,
        "total_workers": len(users),
        "records": results
    }

@router.get("/export-csv")
def export_timesheet_csv(target_date: Optional[str] = None, db: Session = Depends(get_db)):
    data = get_timesheet(target_date, db)
    csv_bytes = generate_timesheet_csv(data["records"])
    
    filename = f"tabel_ktz_{data['selected_date']}.csv"
    return Response(
        content=csv_bytes.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

from sqlalchemy import or_

@router.get("/roster")
def get_roster(
    role: Optional[str] = None,
    master_id: Optional[int] = None,
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    token_user=Depends(get_current_user_optional),
):
    """
    Roster with live presence for Dispatcher, Boss, and Master.
    Dispatcher/Boss gets all employees or filtered.
    Master gets his subordinates (or all workers if master_id not specified).
    """
    # NOTE: Attendance timestamps are stored with datetime.now() (server local time),
    # so "today" must be computed the same way — not with utcnow().
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = date.today().strftime("%Y-%m-%d")

    q = db.query(User)
    if master_id:
        q = q.filter(User.master_id == master_id)
    if role:
        q = q.filter(User.role == role)
    if query:
        term = f"%{query.strip()}%"
        q = q.filter(
            or_(
                User.full_name.ilike(term),
                User.username.ilike(term),
                User.position.ilike(term)
            )
        )

    users = q.order_by(User.full_name.asc()).all()

    # Also include unregistered workers who checked in today
    unregistered_atts = db.query(Attendance).filter(
        Attendance.user_id.is_(None),
        Attendance.timestamp >= today_start
    ).all()

    results = []
    # IIN is sensitive: only a logged-in BOSS sees it in the roster.
    show_iin = token_user is not None and token_user.role == "BOSS"
    for u in users:
        leave = db.query(Leave).filter(
            Leave.user_id == u.id,
            Leave.status == "APPROVED",
            Leave.start_date <= today_str,
            Leave.end_date >= today_str
        ).first()

        latest_att = db.query(Attendance).filter(
            or_(Attendance.user_id == u.id, Attendance.worker_name == u.full_name),
            Attendance.timestamp >= today_start
        ).order_by(Attendance.timestamp.desc()).first()

        first_in = db.query(Attendance).filter(
            or_(Attendance.user_id == u.id, Attendance.worker_name == u.full_name),
            Attendance.action_type == "CHECK_IN",
            Attendance.timestamp >= today_start
        ).order_by(Attendance.timestamp.asc()).first()

        first_out = db.query(Attendance).filter(
            or_(Attendance.user_id == u.id, Attendance.worker_name == u.full_name),
            Attendance.action_type == "CHECK_OUT",
            Attendance.timestamp >= today_start
        ).order_by(Attendance.timestamp.desc()).first()

        status = "ABSENT"
        if leave:
            status = "LEAVE"
        elif latest_att and latest_att.action_type == "CHECK_IN":
            status = "PRESENT"

        master_user = db.query(User).filter(User.id == u.master_id).first() if u.master_id else None

        results.append({
            "id": u.id,
            "full_name": u.full_name,
            "position": u.position or "Монтер пути",
            "role": u.role,
            "organization": u.organization or "ПЧ-13 (Алматы дистанциясы)",
            "unit_code": u.unit_code or "ПЧ-13",
            "subdivision": u.subdivision or "Участок №3",
            "iin": u.iin if show_iin else None,
            "emp_num": u.emp_num or f"RG-{u.id:04d}",
            "phone": u.phone or "—",
            "photo_url": (latest_att.photo_url if latest_att and latest_att.photo_url else u.photo_url),
            "master_id": u.master_id,
            "master_name": master_user.full_name if master_user else "—",
            "status": status,
            "check_in_time": first_in.timestamp.strftime("%H:%M") if first_in else "—",
            "check_out_time": first_out.timestamp.strftime("%H:%M") if first_out else "—",
            "leave_type": leave.leave_type if leave else None
        })

    # Add unregistered checkins if no role or master filter
    if not master_id and not role:
        seen_names = set(u.full_name for u in users)
        for att in unregistered_atts:
            if att.worker_name and att.worker_name not in seen_names:
                seen_names.add(att.worker_name)
                results.append({
                    "id": None,
                    "full_name": att.worker_name,
                    "position": "Жұмысшы (КПП)",
                    "role": "WORKER",
                    "emp_num": "—",
                    "phone": "—",
                    "photo_url": att.photo_url,
                    "master_id": None,
                    "master_name": "—",
                    "status": "PRESENT" if att.action_type == "CHECK_IN" else "ABSENT",
                    "check_in_time": att.timestamp.strftime("%H:%M") if att.action_type == "CHECK_IN" else "—",
                    "check_out_time": att.timestamp.strftime("%H:%M") if att.action_type == "CHECK_OUT" else "—",
                    "leave_type": None
                })

    return {
        "date": today_str,
        "total": len(results),
        "present_count": sum(1 for r in results if r["status"] == "PRESENT"),
        "absent_count": sum(1 for r in results if r["status"] == "ABSENT"),
        "leave_count": sum(1 for r in results if r["status"] == "LEAVE"),
        "records": results
    }

