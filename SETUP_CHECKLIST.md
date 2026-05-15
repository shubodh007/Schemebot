# GovScheme AI — Setup Checklist

> Check off each item as completed. Estimated time: **45-60 minutes** for a full setup.

## □ 1. Prerequisites

| # | Item | Check | Notes |
|---|------|-------|-------|
| 1.1 | Node.js 20.x+ installed | □ | `node --version` → v20.x |
| 1.2 | Python 3.11+ installed | □ | `python --version` → 3.11+ |
| 1.3 | Poetry installed | □ | `pip install poetry` or `pip install -r requirements.txt` |
| 1.4 | Git installed | □ | `git --version` |
| 1.5 | OpenSSL available | □ | `openssl version` (for generating SECRET_KEY) |

## □ 2. Supabase Project

| # | Action | URL | Value | Check |
|---|--------|-----|-------|-------|
| 2.1 | Create Supabase project | [supabase.com](https://supabase.com) → New project | Project name: `govscheme-ai` | □ |
| 2.2 | Copy Project URL | Settings → API → Project URL | `https://xxxxxxxxxxxx.supabase.co` | □ |
| 2.3 | Copy anon/public key | Settings → API → anon/public | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | □ |
| 2.4 | Copy service_role key | Settings → API → service_role | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | □ |
| 2.5 | Copy DB connection string | Settings → Database → URI | `postgresql+asyncpg://postgres:...@aws-0.ap-south-1.rds.amazonaws.com:6543/postgres` | □ |
| 2.6 | Enable pgvector | SQL Editor → Run: `CREATE EXTENSION IF NOT EXISTS vector;` | □ |
| 2.7 | Enable uuid-ossp | SQL Editor → Run: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";` | □ |
| 2.8 | Enable pg_trgm | SQL Editor → Run: `CREATE EXTENSION IF NOT EXISTS "pg_trgm";` | □ |

## □ 3. Upstash Redis

| # | Action | URL | Value | Check |
|---|--------|-----|-------|-------|
| 3.1 | Create Redis DB | [upstash.com](https://console.upstash.com/) → Create database | Region: same as Supabase | □ |
| 3.2 | Copy Redis URL | Console → Redis Database → REST API → UPSTASH_REDIS_URL | `redis://default:password@apt-marmot-12345.upstash.io:6379` | □ |
| 3.3 | Copy REST Token | Same page → REST API Token | For management operations | □ |

## □ 4. OpenRouter

| # | Action | URL | Value | Check |
|---|--------|-----|-------|-------|
| 4.1 | Create OpenRouter account | [openrouter.ai](https://openrouter.ai/) → Sign up | □ |
| 4.2 | Generate API key | [openrouter.ai/keys](https://openrouter.ai/keys) → Create key | `sk-or-v1-xxxxxxxxxxxxxxxx` | □ |
| 4.3 | Verify free models available | [openrouter.ai/models](https://openrouter.ai/models) → Filter: `:free` | Check trinity-large-thinking, nemotron-3-super are listed | □ |

## □ 5. Google AI Studio

| # | Action | URL | Value | Check |
|---|--------|-----|-------|-------|
| 5.1 | Create Google AI API key | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → Create API key | `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX` | □ |

## □ 6. Optional Services

| # | Service | URL | Value | Check |
|---|---------|-----|-------|-------|
| 6.1 | Sentry (error tracking) | [sentry.io](https://sentry.io) → Create FastAPI project | DSN: `https://key@o123.ingest.sentry.io/123` | □ |
| 6.2 | PostHog (analytics) | [us.posthog.com](https://us.posthog.com) → Create project | API key: `phc_xxxxxxxxxxxx` | □ |

## □ 7. Backend Setup

| # | Action | Command | Check |
|---|--------|---------|-------|
| 7.1 | Navigate to backend | `cd backend` | □ |
| 7.2 | Install dependencies | `poetry install` or `pip install -r requirements.txt` | □ |
| 7.3 | Copy env file | `cp .env.example .env` | □ |
| 7.4 | Generate SECRET_KEY | `openssl rand -hex 64` → paste into `.env` | □ |
| 7.5 | Fill in all .env values | See section 2-6 for values | □ |
| 7.6 | Run database migrations | `alembic upgrade head` | □ |
| 7.7 | Start API server | `uvicorn app.main:app --reload --port 8000` | □ |
| 7.8 | Verify health endpoint | `curl http://localhost:8000/api/v1/health` → `{"status":"ok"}` | □ |

## □ 8. Frontend Setup

| # | Action | Command | Check |
|---|--------|---------|-------|
| 8.1 | Navigate to frontend | `cd frontend` | □ |
| 8.2 | Install dependencies | `npm install` | □ |
| 8.3 | Copy env file | `cp .env.local.example .env.local` | □ |
| 8.4 | Fill in .env.local | Supabase URL + anon key + backend URL | □ |
| 8.5 | Start dev server | `npm run dev` | □ |
| 8.6 | Open in browser | [http://localhost:3000](http://localhost:3000) | □ |

## □ 9. Background Worker (Optional)

| # | Action | Command | Check |
|---|--------|---------|-------|
| 9.1 | In separate terminal | `cd backend` | □ |
| 9.2 | Start Arq worker | `python -m arq arq_app.WorkerSettings` | □ |

## □ 10. Verification

| # | Test | Expected Result | Check |
|---|------|----------------|-------|
| 10.1 | Frontend loads | Landing page with "Know Every Scheme You Qualify For" | □ |
| 10.2 | Register a user | POST /api/v1/auth/register → 201 | □ |
| 10.3 | Login | POST /api/v1/auth/login → access_token | □ |
| 10.4 | List schemes | GET /api/v1/schemes → `{"schemes":[...]}` | □ |
| 10.5 | Create chat session | POST /api/v1/chat/sessions → 201 | □ |
| 10.6 | AI chat response | POST /api/v1/chat/sessions/{id}/messages → SSE stream | □ |
| 10.7 | Document upload | POST /api/v1/documents/upload → 201 | □ |
| 10.8 | Eligibility check | POST /api/v1/schemes/eligibility-check → matches array | □ |
| 10.9 | Admin dashboard | GET /api/v1/admin/analytics → 200 | □ |
| 10.10 | Frontend chat flow | Login → Chat → Send message → See streaming response | □ |

## □ 11. Production Deployment

| # | Action | Details | Check |
|---|--------|---------|-------|
| 11.1 | Deploy backend to Railway | Connect repo → Set root dir: `backend` → Build: `pip install -r requirements.txt` → Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | □ |
| 11.2 | Deploy worker to Railway | Same project → Add service → Start: `python -m arq arq_app.WorkerSettings` | □ |
| 11.3 | Deploy frontend to Vercel | Connect repo → Root dir: `frontend` → Framework: Next.js → Build: `npm run build` | □ |
| 11.4 | Set Railway environment variables | All vars from `.env` → Railway dashboard | □ |
| 11.5 | Set Vercel environment variables | `NEXT_PUBLIC_API_URL` → Railway prod URL | □ |
| 11.6 | Verify production health | `https://your-backend.railway.app/api/v1/health` → `{"status":"ok"}` | □ |
| 11.7 | Verify production frontend | `https://your-site.vercel.app` → loads | □ |

---

## Quick Reference: Required Values by File

### `backend/.env` — 10 keys required

```
SUPABASE_URL          = https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY     = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_URL       = postgresql+asyncpg://postgres:...:6543/postgres
SECRET_KEY            = <openssl rand -hex 64 output>
OPENROUTER_API_KEY    = sk-or-v1-xxxxxxxxxxxxxxxx
UPSTASH_REDIS_URL     = redis://default:...@apt-marmot-12345.upstash.io:6379
GOOGLE_AI_API_KEY     = AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX
GOOGLE_AI_STUDIO_API_KEY = AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX
```

### `frontend/.env.local` — 2 keys required

```
NEXT_PUBLIC_SUPABASE_URL    = https://xxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL         = http://localhost:8000/api/v1
```

---

**Time Breakdown:**
- API key generation: 15 min
- Backend setup: 15 min
- Frontend setup: 10 min
- Verification: 10 min
- **Total: ~50 min**
