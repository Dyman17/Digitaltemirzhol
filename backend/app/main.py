import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import STORAGE_DIR, BASE_DIR, CORS_ORIGINS
from app.core.database import engine, Base, ensure_schema
from app.routers import auth, attendance, naryad, leaves, kiosk, chat

# Create database tables (runs on import; safe for Render/Vercel cold start)
# + backfill columns for DBs created by older app versions.
ensure_schema()

app = FastAPI(
    title="Digital Temirzhol Enterprise API",
    description="Қазақстан Темір Жолы (ҚТЖ) процестерін цифрландыру: Фото-чекин, Smart Наряд-допуск №451, Табель және больничный",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Bearer-tokens in Authorization header: no cookies needed, so credentials off
    # (browsers reject allow_credentials=True combined with "*").
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(attendance.router)
app.include_router(naryad.router)
app.include_router(leaves.router)
app.include_router(kiosk.router)
app.include_router(chat.router)

# Mount Storage
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

@app.get("/api/health")
def health():
    return {
        "status": "ONLINE",
        "system": "Digital Temirzhol • ҚТЖ Өндірістік жүйесі",
        "version": "3.0.0"
    }


@app.get("/health")
def health_root():
    return {"status": "ONLINE"}

# Mount Frontend
FRONTEND_DIR = BASE_DIR.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
