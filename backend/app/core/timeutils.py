"""Single source of wall-clock time for user-facing timestamps.

Servers (Render) run in UTC, users live in Kazakhstan (UTC+5, Asia/Almaty).
All timestamps shown to people — check-ins, chat, audit, PDFs — must use
Almaty wall time, otherwise the timesheet lies by 5-6 hours.

Storage format stays naive (no tzinfo) to match existing rows; only the
"which hour is it" basis changes. Technical expiries (JWT exp, reset codes)
keep using UTC on both sides and are untouched.
"""
import os
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo  # needs `tzdata` pkg on slim images
    _TZ = ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Almaty"))
except Exception:
    # Fallback: fixed Kazakhstan offset (UTC+5 nationwide since 2024)
    _TZ = timezone(timedelta(hours=5))


def now_local() -> datetime:
    """Naive datetime of 'now' in the app timezone."""
    return datetime.now(_TZ).replace(tzinfo=None)


def today_start_local() -> datetime:
    return now_local().replace(hour=0, minute=0, second=0, microsecond=0)
