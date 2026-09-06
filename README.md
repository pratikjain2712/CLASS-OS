# ClassOS — Question Paper Generator

SaaS platform for Indian coaching institutes to generate question papers from publisher content.

## Quick Start (Docker Compose)

```bash
# 1. Start all services (DB, Redis, API, Frontend)
docker compose up

# 2. Apply migrations (auto-applied via initdb on first start)

# 3. Seed demo data
cd backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/classos \
  python ../scripts/seed_demo.py

# 4. Open http://localhost:5173
# Login: priya@arihant.edu / teacher123
```

## Services

| Service   | URL                        | Notes                     |
|-----------|----------------------------|---------------------------|
| Frontend  | http://localhost:5173      | React + Vite + Tailwind   |
| API       | http://localhost:8000      | FastAPI                   |
| API Docs  | http://localhost:8000/docs | Swagger UI                |
| DB        | localhost:5432             | PostgreSQL + pgvector     |
| Redis     | localhost:6379             | Job queue                 |

## Development (no Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL etc.
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Key API Endpoints

```
POST /api/auth/login                    → get JWT token
GET  /api/publishers                    → list publishers
GET  /api/publishers/{id}/books         → books by publisher
GET  /api/publishers/books/{id}/chapters
GET  /api/templates                     → paper templates
GET  /api/papers/availability           → question count check (Step 4)
POST /api/papers/generate               → generate paper (bank mode)
GET  /api/papers/{id}                   → paper + questions
PUT  /api/papers/{id}/questions/{pq_id}/swap
POST /api/papers/{id}/finalize
GET  /api/questions                     → browse question bank
POST /api/admin/questions/bulk-import   → Excel import
```

## Project Structure

```
CLASS-OS/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI entry point
│   │   ├── config.py            Settings (pydantic-settings)
│   │   ├── database.py          SQLAlchemy async engine
│   │   ├── models/              ORM models
│   │   ├── routers/             API route handlers
│   │   ├── schemas/             Pydantic request/response models
│   │   ├── services/            Business logic
│   │   └── middleware/auth.py   JWT auth
│   ├── migrations/
│   │   └── 001_initial.sql      Full schema + seed data
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── pages/               One file per route
│       ├── hooks/useAuth.ts     Zustand auth store
│       ├── lib/api.ts           Axios client
│       └── types/               TypeScript interfaces
├── scripts/
│   └── seed_demo.py             Demo data seeder
├── docs/
│   └── question-paper-generator-plan.md
└── docker-compose.yml
```

## Phase Roadmap

| Phase | Scope |
|-------|-------|
| **1 (now)** | Bank-mode generation, templates, bulk Excel import, teacher UI |
| **2** | RAG pipeline, AI generation (Claude API), credit system |
| **3** | PDF/DOCX export, QR codes, analytics dashboards |
