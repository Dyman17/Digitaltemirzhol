# Digital Temirzhol — деплой: Render (backend) + Vercel (frontend)

Архитектура:
- **Render Web Service** `digitaltemirzhol-api` — FastAPI + Postgres, заодно раздаёт
  фронтенд (монолит, работает сразу без Vercel).
- **Vercel** — статический `frontend/`, ходит в API на Render через `window.DT_API_BASE`.

## 1. Render (Blueprint, в 1 клик)

1. Залить этот репозиторий на GitHub.
2. Render Dashboard → **New → Blueprint** → выбрать репозиторий
   (файл `render.yaml` подхватится автоматически).
3. Нажать **Apply**. Создадутся:
   - `digitaltemirzhol-db` (Postgres),
   - `digitaltemirzhol-api` (Python, `DATABASE_URL` и `SECRET_KEY` уже связаны),
   - `digitaltemirzhol-frontend` (статика, опционально).
4. Дождаться деплоя, открыть URL вида
   `https://digitaltemirzhol-api.onrender.com` — там и API (`/api/health`),
   и весь фронтенд. Демо-логины (создаются `backend/seed_roles.py`,
   пароль = логин): `boss` / `dispatcher` / `master` / `worker`.
   ⚠️ Это стартовые аккаунты для защиты диплома — в проде смените пароли
   и поставьте `DEMO_SHOW_RESET_CODE=false`.
5. В настройках `digitaltemirzhol-frontend` проверить env `API_URL` —
   должен совпадать с реальным URL API (Blueprint ставит по умолчанию
   `https://digitaltemirzhol-api.onrender.com`; если имя сервиса другое —
   поправить и сделать Manual Deploy).

Важно про роли: самозванец не станет бастыгом — самостоятельная регистрация
`BOSS`/`DISPATCHER` уходит на подтверждение действующему Бастыгу
(вкладка «Жаңа тіркелулер» в кабинете). `WORKER`/`MASTER` входят сразу.

QR на бумаге (без экранов): диспетчер в своём кабинете жмёт «Көшіру» у нужного
КПП → получается ссылка вида `.../go.html?c=1` (`go.html` — чистая страница
только-чекин: камера + КІРДІМ/ШЫҚТЫМ, без лишнего) → по ней генерируется QR
(любой генератор) → распечатать и приклеить на входе. Работник сканирует →
фото сохраняется → «Келдім/Кеттім». Отдельного киоск-экрана нет — только бумага.

Сброс пароля: ссылка на странице входа → код на телефон/email.
Настройте SMTP в env (`SMTP_HOST/PORT/USER/PASSWORD/FROM`, пример для Gmail
в `backend/.env.example`) — код уйдёт письмом. Без SMTP работает демо-режим:
код показывается на экране (`DEMO_SHOW_RESET_CODE=true` для защиты диплома).

Подписи с доски — рабочие: то, что нарисовано при регистрации, ставится на
наряды (мастер/бастык/диспетчер), на больничные и встраивается в PDF №451.
Если человек не рисовал — генерируется факсимиле-штамп.

Журнал событий: у Бастыга вкладка «Журнал событий» — кто, когда, что сделал
(входы, чекины, наряды, больничные, растаулар), с фильтром по типу.
Хранится в таблице `audit_log` (`GET /api/audit/list`).

Навигация единая: `frontend/js/layout.js` рисует общую шапку на всех 9
страницах (Басты бет • Фото-чекин • Киоск • Менің кабинетім • профиль).

Переменные окружения API (`backend/.env.example` — образец):
`DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS` (для продакшена лучше перечислить
домены вместо `*`), `STORAGE_DIR`, `ACCESS_TOKEN_EXPIRE_MINUTES`.

## 2. Vercel (фронтенд)

1. Vercel → **Add New → Project** → Import этот репозиторий.
   `vercel.json` уже указывает `outputDirectory: frontend`, ничего менять не надо.
2. В **Settings → Environment Variables** добавить:
   - `API_URL = https://digitaltemirzhol-api.onrender.com` (реальный URL с Render).
   
   Build-скрипт запишет его в `frontend/js/config.js` как `window.DT_API_BASE`.
3. **Deploy**. Проверка: открыть сайт, залогиниться как `boss`/`boss`.

Без переменной `API_URL` фронтенд попробует тот же origin (работает только если
API и фронт на одном домене, как монолит на Render).

## 3. Локально

```bash
pip install -r backend/requirements.txt
python backend/seed_roles.py
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend
# открыть http://127.0.0.1:8000
```
