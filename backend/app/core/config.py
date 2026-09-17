import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
SIGNATURES_DIR = STORAGE_DIR / "signatures"
FACE_PROFILES_DIR = STORAGE_DIR / "face_profiles"
LEAVES_DIR = STORAGE_DIR / "leaves_docs"
NARYAD_DIR = STORAGE_DIR / "naryad_docs"

for d in [STORAGE_DIR, SIGNATURES_DIR, FACE_PROFILES_DIR, LEAVES_DIR, NARYAD_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _resolve_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # Render/Heroku legacy scheme fix for SQLAlchemy + psycopg2
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url
    return f"sqlite:///{BASE_DIR}/smartrail.db"


DATABASE_URL = _resolve_database_url()
SECRET_KEY = os.getenv("SECRET_KEY", "smartrail-enterprise-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

# Comma-separated list, e.g. "https://xxx.vercel.app,https://xxx.onrender.com"
# "*" is allowed for a demo deploy; for production set explicit domains.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
