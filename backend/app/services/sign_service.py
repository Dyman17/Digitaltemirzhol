"""Board signatures: the PNG drawn by the user on the white board at registration.

If the user never drew anything (blank canvas) or the file is gone, a facsimile
stamp is generated instead — so approvals always carry a visible signature.
"""
from pathlib import Path
from app.core.config import STORAGE_DIR, SIGNATURES_DIR
from app.services.pdf_service import create_facsimile_signature

# Blank white-board PNGs are tiny; anything below this is "no real signature".
MIN_SIGNATURE_BYTES = 1200


def storage_path_for(url: str) -> Path | None:
    if not url or not url.startswith("/storage/"):
        return None
    return STORAGE_DIR / url[len("/storage/"):]


def has_real_signature(signature_url: str | None) -> bool:
    path = storage_path_for(signature_url or "")
    return bool(path and path.exists() and path.stat().st_size >= MIN_SIGNATURE_BYTES)


def resolve_signature(user, role_label: str = "ПЧ") -> str:
    """Returns a /storage/... URL: user's board signature or a generated facsimile."""
    if has_real_signature(getattr(user, "signature_url", None)):
        return user.signature_url
    target = SIGNATURES_DIR / f"facsimile_{user.id}.png"
    if not (target.exists() and target.stat().st_size > 0):
        create_facsimile_signature(user.full_name, target, role=role_label)
    return f"/storage/signatures/{target.name}"
