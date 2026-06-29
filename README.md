# GrantAssist AI

A web platform that helps researchers discover global research funding opportunities, manage academic profiles (including Google Scholar sync), and draft grant applications using LLM-assisted writing with automatic reference management.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python FastAPI (async) |
| Database | PostgreSQL with SQLAlchemy (async) ORM |
| Vector DB | Weaviate Cloud for semantic search |
| Cache | Redis (Upstash free tier) |
| Task Queue | Huey (Redis-backed) |
| Email | SendGrid |
| LLM | OpenRouter (primary), Google AI Studio (fallback) |

## Features

- **User Authentication** - Email/password registration and login with JWT tokens
- **Grant Discovery** - Aggregate grants from Grants.gov and FWF Open API with keyword and semantic search
- **Academic Paper Search** - Query OpenAlex, Crossref, Semantic Scholar, and arXiv in parallel with deduplication
- **Reference Management** - Format citations in APA, MLA, Chicago, and BibTeX via Zotero API
- **AI-Assisted Drafting** - LLM-powered grant proposal section generation (Background, Goals, Methodology, Outcomes, References)
- **Google Scholar Sync** - Weekly background sync of publications, h-index, and citation counts
- **Email Alerts** - Keyword-based grant alert subscriptions with daily digest emails
- **Dashboard** - Track saved grants, application status, and upcoming deadlines

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── config.py           # Settings and environment config
│   │   ├── database.py         # SQLAlchemy async engine and session
│   │   ├── main.py             # FastAPI app with CORS and routers
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic (auth, grants, papers, LLM, etc.)
│   │   ├── routers/            # API endpoint handlers
│   │   ├── tasks/              # Huey background tasks (scheduler)
│   │   └── utils/              # Dependencies, Redis client
│   ├── tests/                  # Comprehensive unit tests (150+ tests)
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/         # Layout, ProtectedRoute
│   │   ├── pages/              # All app pages
│   │   ├── stores/             # Zustand auth store
│   │   ├── lib/                # API client, utilities
│   │   └── types/              # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── deployment/
│   ├── render.yaml             # Render Blueprint
│   └── vercel.json             # Vercel config
├── docker-compose.yml          # Local development
└── .env.example                # Environment variable template
```

## Quick Start (Local Development)

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.12+

### 1. Clone and Configure

```bash
git clone https://github.com/dkibaara2025/DReseachFinder.git
cd DReseachFinder
cp .env.example .env
# Edit .env with your API keys (optional for basic local dev)
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, Weaviate, the backend (port 8000), and frontend (port 5173).

### 3. Manual Setup (without Docker)

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT token |
| POST | `/auth/logout` | Logout |
| GET | `/profile` | Get user profile |
| PUT | `/profile` | Update profile |
| GET | `/profile/extended` | Get extended profile with publications |
| POST | `/profile/sync-scholar` | Trigger Scholar sync |
| GET | `/grants` | Search grants with filters |
| POST | `/grants` | Fetch and cache grants from external APIs |
| GET | `/grants/{id}` | Get grant details |
| POST | `/grants/save` | Save a grant |
| GET | `/grants/saved/list` | List saved grants |
| GET | `/papers` | Search papers across all sources |
| POST | `/references` | Format citations |
| GET/POST | `/applications` | List/create applications |
| GET/PUT/DELETE | `/applications/{id}` | CRUD for application |
| POST | `/applications/{id}/generate` | AI-generate a section |
| GET | `/applications/{id}/export` | Export application |
| GET/POST | `/alerts` | List/create alert subscriptions |
| DELETE | `/alerts/{id}` | Delete an alert |
| GET | `/health` | Health check |

## Running Tests

```bash
cd backend
pip install pytest pytest-asyncio httpx aiosqlite
python -m pytest tests/ -v
```

All 150+ tests cover:
- Auth service (password hashing, JWT tokens, registration, authentication)
- Grant service (caching, search with filters, date parsing)
- Paper service (deduplication, abstract reconstruction)
- Reference service (identifier detection, citation formatting in all styles)
- LLM service (prompt building)
- Scholar service (profile ID extraction, HTML parsing)
- Email service (alert and reminder email templates)
- Redis client (graceful fallback without Redis)
- All Pydantic schemas (validation)
- API endpoints (auth, grants, applications, alerts with full CRUD)

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `REDIS_URL` | Redis connection string | No (graceful fallback) |
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM | For AI features |
| `GOOGLE_AI_STUDIO_API_KEY` | Google AI fallback | For AI features |
| `SENDGRID_API_KEY` | SendGrid email API key | For email alerts |
| `SERPAPI_API_KEY` | SerpApi for Scholar data | For Scholar sync |
| `WEAVIATE_URL` | Weaviate Cloud URL | For semantic search |
| `ZOTERO_API_KEY` | Zotero API key | For reference formatting |

## Deployment

### Frontend (Vercel)

1. Connect your GitHub repo to Vercel
2. Set root directory to `frontend`
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add environment variables (see `deployment/vercel.json`)

### Backend (Render)

1. Create a new Web Service on Render
2. Use the `deployment/render.yaml` Blueprint
3. Set environment variables
4. The service uses the `backend/Dockerfile`

### Database (Supabase)

1. Create a free Supabase project
2. Copy the PostgreSQL connection string to `DATABASE_URL`
3. Tables are auto-created on first startup via SQLAlchemy

### Redis (Upstash)

1. Create a free Upstash Redis database
2. Copy the connection URL to `REDIS_URL`

## License

MIT
