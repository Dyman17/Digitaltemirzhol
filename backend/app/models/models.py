from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # BOSS, DISPATCHER, MASTER, WORKER
    position = Column(String(100), nullable=True)  # Должность (Монтер пути 4-разряда, Дорожный мастер, etc.)
    organization = Column(String(100), default="ПЧ-13 (Алматы дистанциясы)")  # Имя части / Кәсіпорын / Дистанция
    unit_code = Column(String(50), nullable=True)                              # Номер/код части (ПЧ-13, в/ч 25744)
    subdivision = Column(String(100), default="Участок №3, Околоток №10")     # Подразделение / Околоток
    iin = Column(String(12), unique=True, nullable=True)                      # 12 таңбалы ЖСН / ИИН
    birth_date = Column(String(30), nullable=True)                           # Дата рождения
    blood_group = Column(String(20), nullable=True)                          # Группа крови (O(I) Rh+, etc.)
    rank_or_grade = Column(String(50), nullable=True)                        # Разряд / Звание (4-разряд, Сержант)
    safety_briefing_date = Column(String(30), nullable=True)                 # Дата инструктажа ТБ/ПТЭ
    emp_num = Column(String(30), unique=True, nullable=True)  # Табельдік № (RG-00104)
    phone = Column(String(30), nullable=True)
    email = Column(String(100), nullable=True)
    photo_url = Column(String(255), nullable=True)
    face_embedding = Column(Text, nullable=True)  # JSON or feature string for biometric match
    signature_url = Column(String(255), nullable=True)  # Path to transparent PNG signature
    master_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Linked Master for workers
    is_approved = Column(Boolean, default=True)  # BOSS/DISPATCHER self-registrations wait for approval
    created_at = Column(DateTime, default=datetime.utcnow)

    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")
    leaves = relationship("Leave", back_populates="user", cascade="all, delete-orphan", foreign_keys="[Leave.user_id]")
    created_naryads = relationship("Naryad", back_populates="master", foreign_keys="[Naryad.master_id]")
    master = relationship("User", remote_side=[id], backref="subordinates")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    worker_name = Column(String(100), nullable=True)
    photo_url = Column(String(255), nullable=True)
    action_type = Column(String(20), nullable=False)  # CHECK_IN, CHECK_OUT
    timestamp = Column(DateTime, default=datetime.utcnow)
    checkpoint = Column(String(100), default="КПП ПЧ-13 (Бас проходная)")
    note = Column(String(255), nullable=True)

    user = relationship("User", back_populates="attendances")

class Naryad(Base):
    __tablename__ = "naryads"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), unique=True, nullable=False)  # №451-2026/01
    master_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    boss_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dispatcher_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    organization = Column(String(100), default="ПЧ-13 (Алматы дистанциясы)")
    subdivision = Column(String(100), default="Участок №3, Околоток №10")
    work_type = Column(String(150), nullable=False)  # Регулировка стыковых зазоров / Смена рельсовых плетей
    tech_card_no = Column(String(50), nullable=False)  # ТК-16, ТК-28
    location = Column(String(200), nullable=False)  # Станция Алматы-2, Перегон, 42-45 км, ПК-4
    safety_measures = Column(Text, nullable=True)  # JSON-encoded array

    status = Column(String(40), default="PENDING_BOSS")
    # PENDING_BOSS -> APPROVED_BOSS -> PERMITTED_DISPATCHER -> COMPLETED

    plan_start = Column(String(50), nullable=True)
    plan_end = Column(String(50), nullable=True)
    actual_end = Column(String(50), nullable=True)
    
    boss_signature_url = Column(String(255), nullable=True)
    dispatcher_signature_url = Column(String(255), nullable=True)
    master_signature_url = Column(String(255), nullable=True)
    pdf_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    master = relationship("User", back_populates="created_naryads", foreign_keys=[master_id])
    boss = relationship("User", foreign_keys=[boss_id])
    dispatcher = relationship("User", foreign_keys=[dispatcher_id])
    brigade_members = relationship("NaryadBrigade", back_populates="naryad", cascade="all, delete-orphan")

class NaryadBrigade(Base):
    __tablename__ = "naryad_brigades"

    id = Column(Integer, primary_key=True, index=True)
    naryad_id = Column(Integer, ForeignKey("naryads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    briefing_signed = Column(Boolean, default=True)
    signed_at = Column(DateTime, default=datetime.utcnow)

    naryad = relationship("Naryad", back_populates="brigade_members")
    user = relationship("User")

class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)  # SICK_LEAVE (Больничный), VACATION (Отпуск), MATERNITY (Декрет)
    start_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(20), nullable=False)    # YYYY-MM-DD
    document_url = Column(String(255), nullable=True) # Photo/screenshot/PDF of hospital note
    status = Column(String(20), default="PENDING")   # PENDING, APPROVED, REJECTED
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    boss_signature_url = Column(String(255), nullable=True)  # approver's board signature snapshot
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="leaves", foreign_keys=[user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    target_role = Column(String(20), nullable=True)  # BOSS, DISPATCHER, ALL
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(30), default="INFO")  # ATTENDANCE, NARYAD, LEAVE
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class PasswordResetCode(Base):
    """One-time 6-digit codes for password reset (hashed, 10-minute expiry)."""

    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    """Unified event journal: who did what and when (общая таблица событий)."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_name = Column(String(100), nullable=True)
    actor_role = Column(String(20), nullable=True)
    action = Column(String(40), nullable=False, index=True)  # e.g. NARYAD_APPROVE
    entity = Column(String(20), nullable=True)  # naryad | leave | user | attendance
    entity_id = Column(Integer, nullable=True)
    detail = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkPoint(Base):
    """Managed by dispatcher: checkpoints (КПП, used by QR check-in flow)
    and track sections (участки/перегоны, shown on the monitoring board)."""

    __tablename__ = "work_points"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # e.g. "КПП ПЧ-13", "Перегон Алматы-1 — Бурундай"
    kind = Column(String(20), nullable=False, default="checkpoint")  # checkpoint | section
    location = Column(String(200), nullable=True)  # free note: км, ПК, станция
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

