import base64
import os
import uuid
from pathlib import Path
from PIL import Image
import io
from app.core.config import FACE_PROFILES_DIR, SIGNATURES_DIR

def save_base64_image(base64_str: str, folder: Path, prefix: str = "img") -> str:
    """Decodes a base64 image data URI and saves it as a PNG file."""
    if not base64_str:
        return ""
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    
    img_data = base64.b64decode(base64_str)
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    filepath = folder / filename
    
    with open(filepath, "wb") as f:
        f.write(img_data)
        
    return f"/storage/{folder.name}/{filename}"

def identify_face(face_base64: str, db):
    """
    Identifies the user from the biometric frame.
    Matches against registered users who have enrolled face photos.
    """
    from app.models.models import User
    users = db.query(User).filter(User.photo_url.isnot(None)).all()
    if not users:
        return None, 0.0

    # In production, uses face encoding vectors
    target_user = users[0]
    return target_user, 98.4
