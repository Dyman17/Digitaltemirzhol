from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import DATABASE_URL

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
# Render Postgres may require SSL; psycopg2 handles it via URL params (?sslmode=require)
engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """Create missing tables and backfill columns for DBs made by older versions."""
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            if DATABASE_URL.startswith("sqlite"):
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
                if "is_approved" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 1"))
                    conn.execute(text("UPDATE users SET is_approved = 1 WHERE is_approved IS NULL"))
            else:
                exists = conn.execute(
                    text("SELECT 1 FROM information_schema.columns "
                         "WHERE table_name='users' AND column_name='is_approved'")
                ).first()
                if not exists:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT TRUE"))
    except Exception as e:
        print(f"Schema check warning: {e}")
