# GovScheme AI

**AI-powered civic platform** that helps Indian citizens discover, understand, and apply for government welfare schemes they qualify for. Supports English, Hindi, and Telugu with multi-model AI (OpenRouter/Claude/Gemini/GPT-4o/Groq).

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    VERCEL (Frontend)                      │
│  Next.js 15 · App Router · TailwindCSS · shadcn/ui      │
│  Zustand · TanStack Query · Framer Motion                │
│  Supabase Auth (client-side) · SSE Streaming Chat        │
└────────────────────────┬─────────────────────────────────┘
                         │ BFF Proxy (/api/*)
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    RAILWAY (Backend)                      │
│  FastAPI · SQLAlchemy 2.0 async · Pydantic v2            │
│  OpenRouter (multi-model) · RAG Pipeline                  │
│  pgvector · HyDE · Cross-Encoder Reranker                │
└───────────┬──────────────────────────────┬────────────────┘
            │                              │
            ▼                              ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│    SUPABASE           │    │    UPSTASH REDIS              │
│  ┌────────────────┐   │    │  ┌────────────────────────┐  │
│  │ PostgreSQL     │   │    │  │ Cache (rate limits,    │  │
│  │ + pgvector     │   │    │  │  sessions, API cache)  │  │
│  ├────────────────┤   │    │  ├────────────────────────┤  │
│  │ Auth           │   │    │  │ Arq Queue (scraping,   │  │
│  ├────────────────┤   │    │  │  embedding jobs)       │  │
│  │ Storage        │   │    │  └────────────────────────┘  │
│  └────────────────┘   │    └──────────────────────────────┘
└──────────────────────┘
```

## Prerequisites

- **Node.js** 20.x+ (frontend)
- **Python** 3.11+ (backend)
- **PostgreSQL** 14+ with pgvector extension (or Supabase account)
- **Redis** 7+ (or Upstash account)
- **Poetry** (Python package manager) or `pip`

## Quick Start

### 1. Clone & Install Backend

```bash
cd backend
poetry install
# or: pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (see below)
```

### 3. Start Backend

```bash
# Terminal 1: API server
uvicorn app.main:app --reload --port 8000

# Terminal 2: Background worker (optional)
python -m arq arq_app.WorkerSettings
```

### 4. Install & Start Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### 5. Verify

```bash
# Backend health check
curl http://localhost:8000/api/v1/health
# → {"status": "ok"}

# Frontend
open http://localhost:3000
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `SUPABASE_DB_URL` | Yes | PostgreSQL connection string (asyncpg) |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key (primary AI provider) |
| `UPSTASH_REDIS_URL` | Yes | Upstash Redis connection string |
| `GOOGLE_AI_API_KEY` | Recommend | Google AI key (embeddings + Gemini fallback) |
| `SECRET_KEY` | Yes | 64-char hex key for JWT signing |
| `ANTHROPIC_API_KEY` | Optional | Direct Claude API fallback |
| `OPENAI_API_KEY` | Optional | Direct GPT fallback |
| `DEEPSEEK_API_KEY` | Optional | Direct DeepSeek fallback |
| `GROQ_API_KEY` | Optional | Direct Groq fallback |
| `SENTRY_DSN` | Optional | Error tracking |
| `POSTHOG_API_KEY` | Optional | Product analytics |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL (`http://localhost:8000/api/v1`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Supabase anon key |

## AI Provider Setup

### OpenRouter (Primary — Recommended)

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Create a free account and generate an API key
3. Set `OPENROUTER_API_KEY` in your `.env`

Models available via OpenRouter (configured in `app/core/config.py`):
- `anthropic/claude-sonnet-4-20250514` — Scheme eligibility, legal guidance (best reasoning)
- `google/gemini-2.0-flash-lite` — General chat (free)
- `google/gemini-2.0-flash` — Document analysis (free, vision capable)
- `groq/llama-3.1-70b-versatile` — Intent classification, search (fast, free)
- `deepseek/deepseek-chat` — Admin analytics (cost-efficient)

### Google AI (Embeddings + Fallback)

1. Go to [aistudio.google.com](https://aistudio.google.com/apikey)
2. Create an API key (free tier)
3. Set `GOOGLE_AI_API_KEY` in your `.env`

## Database Setup

### Supabase (Recommended)

1. Create a project at [supabase.com](https://supabase.com)
2. Enable pgvector: Go to SQL Editor → Run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

3. Run migrations:

```bash
cd backend
alembic upgrade head
```

4. Get your connection string from: Project Settings → Database → Connection string (URI with `?pgbouncer=true` for production)

### Manual PostgreSQL

```bash
createdb govscheme
psql govscheme -c "CREATE EXTENSION vector; CREATE EXTENSION uuid-ossp; CREATE EXTENSION pg_trgm;"
cd backend && alembic upgrade head
```

## Verification

After starting both servers, verify the full stack:

```bash
# 1. Backend health
curl http://localhost:8000/api/v1/health
# → {"status":"ok"}

# 2. List schemes (no auth needed)
curl http://localhost:8000/api/v1/schemes
# → {"schemes":[],"total":0,...}

# 3. Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass1","full_name":"Test User"}'

# 4. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass1"}'
# Returns access_token — use this for authenticated requests

# 5. Frontend loads
open http://localhost:3000
```

## Production Deployment

### Backend → Railway

1. Create a Railway project from your GitHub repo
2. Set the following:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add Railway Postgres + Redis add-ons
4. Set all environment variables from `.env.example`
5. Deploy

Add a **worker** service:
- **Start Command**: `python -m arq arq_app.WorkerSettings`
- No HTTP port needed

### Frontend → Vercel

1. Connect your GitHub repo to Vercel
2. Set:
   - **Root Directory**: `frontend`
   - **Framework**: Next.js
   - **Build Command**: `npm run build`
3. Set environment variables from `.env.local.example`
4. Deploy

Environment variable reference:
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## Project Structure

```
govscheme-ai/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes + middleware
│   │   ├── ai/           # LLM providers, agents, RAG pipeline
│   │   ├── core/         # Config, DB, Redis, security, exceptions
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── repositories/ # Data access layer
│   │   ├── schemas/      # Pydantic v2 request/response schemas
│   │   ├── scraper/      # Government portal scrapers
│   │   └── services/     # Business logic
│   ├── arq_app.py        # Background worker
│   └── alembic/          # Database migrations
├── frontend/
│   ├── app/              # Next.js 15 App Router pages
│   ├── components/       # React components
│   │   ├── ui/           # shadcn/ui primitives
│   │   ├── layout/       # App shell, sidebar, header
│   │   ├── chat/         # Streaming chat UI
│   │   ├── schemes/      # Scheme cards, detail
│   │   └── common/       # Skeleton, error boundary
│   ├── lib/              # API client, stores, hooks, validators
│   └── i18n/             # English, Hindi, Telugu
```

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `alembic upgrade head` fails | Missing pgvector extension | `CREATE EXTENSION vector;` in Supabase SQL Editor |
| AI responses are empty | Missing OPENROUTER_API_KEY | Set it in `.env` and restart backend |
| Frontend shows "Authentication required" | Missing backend URL | Check `NEXT_PUBLIC_API_URL` in `.env.local` |
| Rate limit errors | Too many requests | Wait 60 seconds; default is 20 req/min for chat |
| Redis connection failed | Wrong UPSTASH_REDIS_URL | Check the URL uses `redis://` not `rediss://` |
| File upload fails | File > 10MB | Resize or split the document |
| Scraping returns 0 schemes | Portal HTML structure changed | Check the portal URL is accessible; run `scrape_source` manually |

## Contributing

1. Create a branch: `git checkout -b feature/my-feature`
2. Make changes, add tests
3. Run checks: `cd backend && ruff check . && mypy .`
4. Commit with conventional commits: `feat: add telangana scraper`
5. Push and open a PR

## License

MIT — built for civic technology. Contribute, fork, deploy for your state.
