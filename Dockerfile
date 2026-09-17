FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Frontend раздаётся самим FastAPI (app.mount("/"...)), поэтому копируем и его
COPY frontend/ /app/frontend/

EXPOSE 8000

# Seed демо-пользователей (идемпотентно) + запуск API
CMD sh -c "python seed_roles.py; uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
