from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    full_name: str
    role: str
    organization: Optional[str] = "ПЧ-13 (Алматы дистанциясы)"
    unit_code: Optional[str] = None
    subdivision: Optional[str] = "Участок №3, Околоток №10"
    iin: Optional[str] = None
    birth_date: Optional[str] = None
    blood_group: Optional[str] = None
    rank_or_grade: Optional[str] = None
    safety_briefing_date: Optional[str] = None
    position: Optional[str] = None
    emp_num: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    master_id: Optional[int] = None

class UserRegister(UserBase):
    password: str
    photo_base64: Optional[str] = None
    signature_base64: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordResetRequest(BaseModel):
    identifier: str  # Email or Phone number (or username)

class PasswordResetConfirm(BaseModel):
    identifier: str
    code: str
    new_password: str

class UserResponse(UserBase):
    id: int
    photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AttendanceCheckIn(BaseModel):
    worker_name: Optional[str] = None
    user_id: Optional[int] = None  # legacy terminal input; ignored when JWT is present
    photo_base64: Optional[str] = None
    face_image_base64: Optional[str] = None
    action_type: str  # CHECK_IN or CHECK_OUT
    checkpoint: Optional[str] = "КПП ПЧ-13 (Бас проходная)"
    checkpoint_id: Optional[int] = None  # КПП from dispatcher-managed work points (?c=...)
    kiosk_token: Optional[str] = None  # dynamic QR token from the entrance screen (?k=...)

class AttendanceResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_position: str
    emp_num: str
    action_type: str
    timestamp: str
    confidence: float
    message: str

class NaryadCreate(BaseModel):
    organization: Optional[str] = "ПЧ-13 (Алматы дистанциясы)"
    subdivision: Optional[str] = "Участок №3, Околоток №10"
    work_type: str
    tech_card_no: str
    location: str
    safety_measures: List[str] = []
    plan_start: str
    plan_end: str
    brigade_user_ids: List[int] = []

class NaryadApproveBoss(BaseModel):
    naryad_id: int

class NaryadPermitDispatcher(BaseModel):
    naryad_id: int
    tech_window_info: Optional[str] = "Разрешено технологическое окно с 10:00 до 14:00"

class NaryadComplete(BaseModel):
    naryad_id: int
    actual_end_time: str
    comment: Optional[str] = "Рабочее место убрано, путь освобожден, сигналы сняты"

class LeaveCreate(BaseModel):
    leave_type: str  # SICK_LEAVE, VACATION, MATERNITY
    start_date: str
    end_date: str
    document_base64: Optional[str] = None
    comment: Optional[str] = None

class LeaveApprove(BaseModel):
    leave_id: int
    status: str = "APPROVED"  # APPROVED or REJECTED

class ChatMessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    text: str

class ChatMessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    sender_role: str
    receiver_id: int
    receiver_name: str
    text: str
    created_at: str
