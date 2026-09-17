from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import random
import secrets

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, needs_rehash, create_access_token,
    get_current_user_optional, require_roles, MIN_PASSWORD_LENGTH,
)
from app.core.config import FACE_PROFILES_DIR, SIGNATURES_DIR, DEMO_SHOW_RESET_CODE
from app.models.models import User, PasswordResetCode
from app.schemas.schemas import UserRegister, UserLogin, UserResponse, PasswordResetRequest, PasswordResetConfirm
from app.services.face_service import save_base64_image

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Roles that require an existing BOSS to approve the new account.
# Anyone can self-register as WORKER/MASTER; BOSS/DISPATCHER wait for approval.
GATED_ROLES = ("BOSS", "DISPATCHER")

PUBLIC_USER_FIELDS = [
    "id", "username", "full_name", "role", "organization", "unit_code",
    "subdivision", "iin", "birth_date", "blood_group", "rank_or_grade",
    "safety_briefing_date", "position", "emp_num", "photo_url",
    "signature_url", "master_id",
]


def user_to_dict(u: User) -> dict:
    return {f: getattr(u, f) for f in PUBLIC_USER_FIELDS}

@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    if data.role not in ("WORKER", "MASTER", "DISPATCHER", "BOSS"):
        raise HTTPException(status_code=400, detail="Белгісіз рөл")
    if not data.password or len(data.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Құпиясөз кем дегенде {MIN_PASSWORD_LENGTH} таңбадан тұруы тиіс",
        )
    if data.iin and (len(data.iin) != 12 or not data.iin.isdigit()):
        raise HTTPException(status_code=400, detail="ЖСН 12 саннан тұруы тиіс")
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
        # BOSS/DISPATCHER self-registrations wait for approval by an active BOSS
        is_approved=(data.role not in GATED_ROLES),
        created_at=datetime.utcnow()
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Тіркеу қатесі: {str(e)}")

    if not new_user.is_approved:
        return {
            "status": "PENDING_APPROVAL",
            "message": "Өтінішіңіз қабылданды. Бастық аккаунтты растаған соң кіре аласыз.",
            "user": user_to_dict(new_user),
        }

    token = create_access_token({"sub": new_user.username, "role": new_user.role, "id": new_user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_to_dict(new_user),
    }

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Логин немесе құпиясөз қате")

    # Transparently upgrade legacy demo hashes to PBKDF2 on successful login
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)
        db.commit()

    if not user.is_approved:
        raise HTTPException(
            status_code=403,
            detail="Аккаунт Бастық тарапынан әлі расталмаған. Растауды күтіңіз.",
        )

    token = create_access_token({"sub": user.username, "role": user.role, "id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_to_dict(user),
    }

@router.get("/users")
def list_users(
    role: str = None,
    db: Session = Depends(get_db),
    token_user=Depends(get_current_user_optional),
):
    # Only approved accounts are listed; IIN/phone stay hidden from guests.
    query = db.query(User).filter(User.is_approved == True)  # noqa: E712
    if role:
        query = query.filter(User.role == role)
    users = query.all()
    result = []
    for u in users:
        d = user_to_dict(u)
        if token_user is None:
            d.pop("iin", None)
            d.pop("phone", None)
            d.pop("email", None)
        result.append(d)
    return result


@router.get("/pending-users")
def pending_users(
    db: Session = Depends(get_db),
    boss=Depends(require_roles("BOSS")),
):
    """Self-registrations waiting for BOSS approval (BOSS/DISPATCHER roles)."""
    users = db.query(User).filter(User.is_approved == False).order_by(User.id.desc()).all()  # noqa: E712
    return [user_to_dict(u) for u in users]


@router.post("/approve-user")
def approve_user(
    data: dict,
    db: Session = Depends(get_db),
    boss=Depends(require_roles("BOSS")),
):
    user_id = (data or {}).get("user_id")
    action = (data or {}).get("action", "APPROVE")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пайдаланушы табылмады")
    if action == "REJECT":
        db.delete(user)
        db.commit()
        return {"status": "SUCCESS", "message": "Өтініш қабылданбады және жойылды"}
    user.is_approved = True
    db.commit()
    return {"status": "SUCCESS", "message": f"{user.full_name} расталды, кіре алады"}

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

RESET_CODE_TTL_MIN = 10


def _hash_code(code: str) -> str:
    return hashlib.sha256(f"reset:{code}".encode("utf-8")).hexdigest()


@router.post("/reset-password/request")
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    raw = (data.identifier or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Телефон нөмірін немесе электрондық поштаны енгізіңіз")

    user = find_user_by_identifier(raw, db)
    if not user:
        raise HTTPException(status_code=404, detail="Бұл байланыс мәліметі (телефон/email) бойынша қызметкер табылмады")

    # Invalidate previous unused codes, then issue a new one (stored hashed, 10 min)
    db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id, PasswordResetCode.used == False  # noqa: E712
    ).update({"used": True})
    code = f"{secrets.randbelow(900000) + 100000}"
    db.add(PasswordResetCode(
        user_id=user.id,
        code_hash=_hash_code(code),
        expires_at=datetime.utcnow() + timedelta(minutes=RESET_CODE_TTL_MIN),
    ))
    db.commit()

    # TODO production: send `code` via SMS/email provider here.
    # In demo mode the code is returned so it can be shown on screen.
    target_contact = user.phone or user.email or user.username
    if "@" in target_contact:
        parts = target_contact.split("@")
        masked = parts[0][:2] + "***@" + parts[1]
    elif len(target_contact) >= 10:
        masked = target_contact[:4] + "***" + target_contact[-4:]
    else:
        masked = target_contact

    resp = {
        "status": "SENT",
        "message": f"6-таңбалы растау коды ({masked}) байланысына жолданды.",
        "username": user.username,
        "masked_contact": masked,
    }
    if DEMO_SHOW_RESET_CODE:
        resp["code"] = code
    return resp

@router.post("/reset-password/confirm")
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    raw = (data.identifier or "").strip()
    code = (data.code or "").strip()
    new_pw = (data.new_password or "").strip()

    if len(new_pw) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Жаңа құпиясөз кем дегенде {MIN_PASSWORD_LENGTH} таңбадан тұруы тиіс",
        )

    user = find_user_by_identifier(raw, db)
    if not user:
        raise HTTPException(status_code=404, detail="Қызметкер табылмады")

    entry = db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id,
        PasswordResetCode.used == False,  # noqa: E712
        PasswordResetCode.code_hash == _hash_code(code),
    ).order_by(PasswordResetCode.id.desc()).first()

    if not entry:
        raise HTTPException(status_code=400, detail="Қате растау коды немесе код сұралмаған")
    if entry.expires_at < datetime.utcnow():
        entry.used = True
        db.commit()
        raise HTTPException(status_code=400, detail="Растау кодының мерзімі өтіп кетті. Қайта сұратыңыз.")

    entry.used = True
    user.password_hash = hash_password(new_pw)
    db.commit()

    token = create_access_token({"sub": user.username, "role": user.role, "id": user.id})

    return {
        "status": "SUCCESS",
        "message": "Құпиясөз сәтті өзгертілді! Жүйеге кіру орындалды.",
        "access_token": token,
        "user": user_to_dict(user),
    }
