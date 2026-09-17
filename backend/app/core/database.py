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


def _column_exists(conn, table: str, column: str) -> bool:
    if DATABASE_URL.startswith("sqlite"):
        cols = [r[1] for r in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()]
        return column in cols
    return conn.execute(
        text("SELECT 1 FROM information_schema.columns "
             "WHERE table_name=:t AND column_name=:c"),
        {"t": table, "c": column},
    ).first() is not None


def _add_column(conn, table: str, ddl: str):
    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def ensure_schema():
    """Create missing tables and backfill columns for DBs made by older versions."""
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            if not _column_exists(conn, "users", "is_approved"):
                default = "1" if DATABASE_URL.startswith("sqlite") else "TRUE"
                _add_column(conn, "users", f"is_approved BOOLEAN DEFAULT {default}")
                conn.execute(text("UPDATE users SET is_approved = 1 WHERE is_approved IS NULL"))
            if not _column_exists(conn, "leaves", "boss_signature_url"):
                _add_column(conn, "leaves", "boss_signature_url VARCHAR(255)")
    except Exception as e:
        print(f"Schema check warning: {e}")
