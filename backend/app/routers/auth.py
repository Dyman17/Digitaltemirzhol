from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import FACE_PROFILES_DIR, SIGNATURES_DIR
from app.models.models import User
from app.schemas.schemas import UserRegister, UserLogin, UserResponse, PasswordResetRequest, PasswordResetConfirm
from app.services.face_service import save_base64_image

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Бұл логинмен пайдаланушы тіркеліп қойған (Логин занят)")

    if data.iin:
        existing_iin = db.query(User).filter(User.iin == data.iin).first()
        if existing_iin:
            raise HTTPException(status_code=400, detail="Бұл ЖСН/ИИН бойынша пайдаланушы бұрын тіркелген")

    # Generate or sanitize unique emp_num
    assigned_emp_num = data.emp_num
    if not assigned_emp_num:
        assigned_emp_num = f"Т-{db.query(User).count() + 101:04d}"
    else:
        # Check if already taken
        collision = db.query(User).filter(User.emp_num == assigned_emp_num).first()
        if collision:
            import random
            assigned_emp_num = f"{assigned_emp_num}-{random.randint(10, 99)}"

    photo_url = None
    if data.photo_base64:
        photo_url = save_base64_image(data.photo_base64, FACE_PROFILES_DIR, prefix=f"face_{data.username}")

    sig_url = None
    if data.signature_base64:
        sig_url = save_base64_image(data.signature_base64, SIGNATURES_DIR, prefix=f"sig_{data.username}")

    new_user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        organization=data.organization or "ПЧ-13 (Алматы дистанциясы)",
        unit_code=data.unit_code or "ПЧ-13",
        subdivision=data.subdivision or "Участок №3, Околоток №10",
        iin=data.iin,
        birth_date=data.birth_date,
        blood_group=data.blood_group,
        rank_or_grade=data.rank_or_grade,
        safety_briefing_date=data.safety_briefing_date,
        position=data.position or "Монтер пути",
        emp_num=assigned_emp_num,
        phone=data.phone,
        email=data.email,
        photo_url=photo_url,
        signature_url=sig_url,
        master_id=data.master_id,
        created_at=datetime.utcnow()
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Тіркеу қатесі: {str(e)}")

    token = create_access_token({"sub": new_user.username, "role": new_user.role, "id": new_user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "organization": new_user.organization,
            "unit_code": new_user.unit_code,
            "subdivision": new_user.subdivision,
            "iin": new_user.iin,
            "birth_date": new_user.birth_date,
            "blood_group": new_user.blood_group,
            "rank_or_grade": new_user.rank_or_grade,
            "safety_briefing_date": new_user.safety_briefing_date,
            "position": new_user.position,
            "emp_num": new_user.emp_num,
            "photo_url": new_user.photo_url,
            "signature_url": new_user.signature_url,
            "master_id": new_user.master_id
        }
    }

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Логин немесе құпиясөз қате")

    token = create_access_token({"sub": user.username, "role": user.role, "id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "organization": user.organization,
            "unit_code": user.unit_code,
            "subdivision": user.subdivision,
            "iin": user.iin,
            "birth_date": user.birth_date,
            "blood_group": user.blood_group,
            "rank_or_grade": user.rank_or_grade,
            "safety_briefing_date": user.safety_briefing_date,
            "position": user.position,
            "emp_num": user.emp_num,
            "photo_url": user.photo_url,
            "signature_url": user.signature_url,
            "master_id": user.master_id
        }
    }

@router.get("/users")
def list_users(role: str = None, db: Session = Depends(get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "organization": u.organization,
            "unit_code": u.unit_code,
            "subdivision": u.subdivision,
            "iin": u.iin,
            "birth_date": u.birth_date,
            "blood_group": u.blood_group,
            "rank_or_grade": u.rank_or_grade,
            "safety_briefing_date": u.safety_briefing_date,
            "position": u.position,
            "emp_num": u.emp_num,
            "photo_url": u.photo_url,
            "signature_url": u.signature_url,
            "master_id": u.master_id
        }
        for u in users
    ]

import random
import time
RESET_CODES = {}

def find_user_by_identifier(raw: str, db: Session):
    clean = raw.strip()
    if not clean:
        return None

    # 1. Direct case-insensitive match on phone, email, username or iin
    user = db.query(User).filter(
        (User.phone == clean) | 
        (User.email.ilike(clean)) | 
        (User.username.ilike(clean)) |
        (User.iin == clean)
    ).first()
    if user:
        return user

    # 2. Match normalized phone digits (ignoring spaces, dashes, parentheses)
    clean_digits = "".join(ch for ch in clean if ch.isdigit())
    if len(clean_digits) >= 6:
        tail = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits
        for u in db.query(User).all():
            if u.phone:
                u_digits = "".join(ch for ch in u.phone if ch.isdigit())
                if u_digits.endswith(tail) or (len(u_digits) >= 10 and clean_digits.endswith(u_digits[-10:])):
                    return u

    return None

@router.post("/reset-password/request")
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    raw = data.identifier.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Телефон нөмірін немесе электрондық поштаны енгізіңіз")

    user = find_user_by_identifier(raw, db)
    if not user:
        raise HTTPException(status_code=404, detail="Бұл байланыс мәліметі (телефон/email) бойынша қызметкер табылмады")

    code = f"{random.randint(100000, 999999)}"
    key = user.username.lower()
    RESET_CODES[key] = {
        "code": code,
        "expires_at": time.time() + 600,
        "user_id": user.id
    }

    target_contact = user.phone or user.email or user.username
    if "@" in target_contact:
        parts = target_contact.split("@")
        masked = parts[0][:2] + "***@" + parts[1]
    elif len(target_contact) >= 10:
        masked = target_contact[:4] + "***" + target_contact[-4:]
    else:
        masked = target_contact

    return {
        "status": "SENT",
        "message": f"6-таңбалы растау коды ({masked}) байланысына жолданды.",
        "username": user.username,
        "masked_contact": masked,
        "code": code
    }

@router.post("/reset-password/confirm")
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    raw = data.identifier.strip()
    code = data.code.strip()
    new_pw = data.new_password.strip()

    if len(new_pw) < 4:
        raise HTTPException(status_code=400, detail="Жаңа құпиясөз кем дегенде 4 таңбадан тұруы тиіс")

    user = find_user_by_identifier(raw, db)
    if not user:
        raise HTTPException(status_code=404, detail="Қызметкер табылмады")

    key = user.username.lower()
    entry = RESET_CODES.get(key)
    if not entry:
        raise HTTPException(status_code=400, detail="Растау коды сұралмаған немесе мерзімі өтіп кеткен")

    if time.time() > entry["expires_at"]:
        del RESET_CODES[key]
        raise HTTPException(status_code=400, detail="Растау кодының мерзімі өтіп кетті. Қайта сұратыңыз.")

    if entry["code"] != code:
        raise HTTPException(status_code=400, detail="Қате растау коды")

    user.password_hash = hash_password(new_pw)
    db.commit()
    del RESET_CODES[key]

    token = create_access_token({"sub": user.username, "role": user.role, "id": user.id})

    return {
        "status": "SUCCESS",
        "message": "Құпиясөз сәтті өзгертілді! Жүйеге кіру орындалды.",
        "access_token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "organization": user.organization,
            "unit_code": user.unit_code,
            "subdivision": user.subdivision,
            "iin": user.iin,
            "position": user.position,
            "emp_num": user.emp_num,
            "photo_url": user.photo_url,
            "signature_url": user.signature_url
        }
    }
