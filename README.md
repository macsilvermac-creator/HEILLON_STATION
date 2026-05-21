# Heillon Legal — Legitimidade Computacional para o Direito

**Versão:** 12.0 — Maio de 2026  
**Estado:** Produção (hardening Fase 12)  
**Testes backend:** `pytest -q`  
**Build frontend:** 28 rotas (`npm run build`)

## Sobre o projeto

A **Estação Heillon** é uma plataforma de **Legitimidade Computacional** que transforma cada ação relevante de IA num registo imutável (**HDR — Heillon Decision Record**) com hash SHA-256, carimbo temporal RFC 3161 e encadeamento criptográfico. Qualquer decisão pode ser auditada, verificada e apresentada como prova técnica.

O **Heillon Legal** é a vertical jurídica dessa estação.

| Recurso | URL |
|:---|:---|
| UI (Vercel) | https://heillon-legal-ui.vercel.app |
| Ecossistema | https://heillon.com |

## Fases concluídas

| Fase | Descrição | Estado |
|:---|:---|:---|
| 1 | HDR Ledger (SHA-256 + RFC 3161) | ✅ |
| 2 | Corpus Normativo + Orquestração | ✅ |
| 3 | DDD + Forense + Diário + Frontend | ✅ |
| 4 | Execução real + Autenticação + Deploy | ✅ |
| 5 | Soberania de modelos + UI/UX | ✅ |
| 6 | PDF/A-1/B + refinamento UI | ✅ |
| 7 | Auditoria (personas + segurança) | ✅ |
| 8 | Mobile PWA | ✅ |
| 9 | Segurança + LGPD | ✅ |
| 10 | Central de Documentação (Docs Hub) | ✅ |
| 11 | Cookies HttpOnly, rate limit, onboarding, E2E smoke | ✅ |
| 12 | PostgreSQL, Redis, Health Dashboard, E2E CI | ✅ |

## Funcionalidades principais

- **HDR Ledger** — registos imutáveis SHA-256 + RFC 3161  
- **Corpus Normativo** — validação pré-execução (LGPD, GDPR, …)  
- **Pacote forense** — PDF/A-1/B + assinatura Ed25519  
- **Soberania de modelos** — Ollama, OpenAI, Anthropic, custom  
- **PWA mobile** — verificação, missões, evidências em campo  
- **Docs Hub** — 10 documentos integrados  
- **Onboarding** — tour guiado de 5 passos  
- **Segurança** — JWT + cookies HttpOnly, rate limit (Redis + fallback), CSP/HSTS  

## Stack tecnológico

| Camada | Tecnologia |
|:---|:---|
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Base de dados | PostgreSQL (produção) / SQLite (dev e testes) |
| Cache / rate limit | Redis 7 (+ fallback em memória) |
| Frontend | Next.js 15, shadcn/ui, Tailwind, Framer Motion |
| Mobile | PWA (`@ducanh2912/next-pwa`) |
| CI/CD | GitHub Actions, Playwright |
| Deploy | Vercel (UI) + Docker Compose (stack local) |

## Arquitetura (DDD)

Sete domínios: **HDR**, **Evidence**, **Mission**, **Normative**, **Forensic**, **User**, **Mobile** — cada um com models, services, repository e API.

```
heillon-legal/
├── backend/app/          # FastAPI + domínios
├── frontend/             # Next.js App Router (28 rotas)
├── supabase/migrations/  # Schema Postgres consolidado
├── docker-compose.yml    # postgres + redis + backend + frontend
└── docs/                 # API, CONTEXT, auditorias, Supabase, segredos
```

## Endpoints principais

| Prefixo | Área |
|:---|:---|
| `/api/v1/auth/*` | Registo, login (JWT + cookie HttpOnly) |
| `/api/v1/ingestion` | Upload de evidências |
| `/api/v1/verify/*` | Verificação pública HDR / cadeia |
| `/api/v1/mission/*` | Planear, aprovar, executar, diário |
| `/api/v1/normative/*` | Corpus normativo |
| `/api/v1/compliance/*` | Relatórios LGPD |
| `/api/v1/forensic/*` | Pacotes forenses |
| `/api/v1/agent-config/*` | Soberania de modelos |
| `/api/v1/mobile/*` | Push e estatísticas mobile |
| `/health`, `/api/v1/health/detailed` | Liveness e painel admin |

Documentação detalhada: [`docs/API-REFERENCE.md`](docs/API-REFERENCE.md), [`docs/CONTEXT.md`](docs/CONTEXT.md).

## Configuração rápida

### Backend (SQLite — desenvolvimento)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### Frontend

```powershell
cd frontend
npm ci
# .env.local (opcional):
# NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
# BACKEND_PROXY_TARGET=http://127.0.0.1:8000
npm run build
npm run dev
```

O proxy em `frontend/next.config.ts` encaminha `/api/v1/*` para o backend (evita CORS em desenvolvimento).

### Stack completa (Docker)

```powershell
cd heillon-legal
$env:AUTH_SECRET_KEY = "sua-chave-jwt-min-32-chars"
$env:FERNET_ENCRYPTION_KEY = "chave-fernet-url-safe-distinta"
docker compose up -d
curl http://localhost:8000/health
```

### PostgreSQL (produção / Supabase)

```env
DATABASE_TYPE=postgresql
POSTGRES_HOST=aws-1-sa-east-1.pooler.supabase.com
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres.ydxjncqtsgikywfgfndx
POSTGRES_PASSWORD=<do-dashboard>
POSTGRES_SSL_MODE=require
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=production
FERNET_ENCRYPTION_KEY=<obrigatório>
AUTH_SECRET_KEY=<obrigatório>
```

Ver [`docs/SUPABASE.md`](docs/SUPABASE.md) e [`docs/SECRETS-AUDIT-FASE12.md`](docs/SECRETS-AUDIT-FASE12.md).

## Variáveis de ambiente (resumo)

| Variável | Descrição |
|:---|:---|
| `DATABASE_TYPE` | `sqlite` ou `postgresql` |
| `DATABASE_URL` | URI SQLite quando `sqlite` |
| `POSTGRES_*` | Ligação Postgres quando `postgresql` |
| `REDIS_URL` | Rate limiting distribuído |
| `AUTH_SECRET_KEY` | JWT (alterar em produção) |
| `FERNET_ENCRYPTION_KEY` | Chaves de agentes (obrigatório em produção) |
| `FORCE_STUB_TIMESTAMP` | Stub RFC3161 (só dev/CI) |
| `MISSION_ROUTES_REQUIRE_AUTH` | Exigir JWT nas rotas de missão |

## Testes

```powershell
# Backend (SQLite)
cd backend
python -m pytest -q

# Frontend build
cd frontend
npm run build

# E2E (backend + frontend a correr)
cd frontend
npx playwright test
```

## Segurança

- Next.js ≥ **15.4.10** (patches RSC — ver [blog Next.js](https://nextjs.org/blog/security-update-2025-12-11)).  
- Não commitar `.env` — ver auditoria Fase 12.  
- Rotas públicas de verificação: considerar WAF e limites adicionais em produção.  

## Licença e contacto

Projeto MVP Heillon / Estação Heillon — consulte a documentação em `docs/` para operação e conformidade LGPD.
