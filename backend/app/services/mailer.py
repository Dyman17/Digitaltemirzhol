"""Password-reset delivery by email (stdlib smtplib, no extra deps).

If SMTP is not configured or sending fails, the caller falls back to demo mode
(code shown on screen) — see DEMO_SHOW_RESET_CODE.
"""
import smtplib
import ssl
from email.message import EmailMessage
from app.core.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_STARTTLS,
)


def smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_reset_code(to_email: str, full_name: str, code: str) -> bool:
    if not smtp_configured():
        return False
    msg = EmailMessage()
    msg["Subject"] = "Digital Temirzhol — құпиясөзді қалпына келтіру коды"
    msg["From"] = SMTP_FROM or SMTP_USER
    msg["To"] = to_email
    msg.set_content(
        f"Сәлеметсіз бе, {full_name}!\n\n"
        f"Құпиясөзді қалпына келтіру коды: {code}\n"
        f"Код 10 минут жарамды.\n\n"
        f"Егер сіз сұратпаған болсаңыз — елемеңіз.\n"
        f"Digital Temirzhol • ҚТЖ өндірістік жүйесі"
    )
    try:
        if SMTP_STARTTLS:
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15, context=context) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        return True
    except Exception as e:
        print(f"SMTP send warning: {e}")
        return False
