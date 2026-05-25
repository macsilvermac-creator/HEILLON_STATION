# Heillon Legal — Legitimidade Computacional para o Direito

**Versão:** 13.0 — Maio de 2026  
**Estado:** Produção (hardening Fase 13)  
**Testes backend:** 73 testes (`pytest -q`)  
**Build frontend:** 31 rotas (`npm run build`)

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
| 13 | ICP-Brasil TSA, headers CSP/HSTS, logging JSON, proxy cookie-aware, PyMuPDF, FTS5, página de conformidade | ✅ |
| **14** | **LGPD técnica: RIPD automático, DPO, retenção de logs, notificação ANPD 72h, consentimento granular** | 🔴 Crítico |
| **15** | **ICP-Brasil qualificada: assinatura A1/A3, PDF/A-3 PAdES embedded, certificado de cliente TSA** | 🟡 Urgente |
| **16** | **CNJ 615/2025 + OAB: classificação de risco IA, auditabilidade, supervisão humana, disclosure** | 🟡 Urgente |
| **17** | **EU AI Act (ago/2026!) + eIDAS 2.0 + GDPR alignment + ISO 27001 foundation** | 🟢 Planeado |
| **18** | **Expansão EUA: Colorado AI Act + ABA Op 512 + CCPA/CPRA + NIST AI RMF** | 🟢 Planeado |
| **19** | **Expansão EAU: UAE PDPL + DIFC + Dubai AI Seal + UAE AI Charter 2024** | 🟢 Planeado |
| **20** | **Expansão Ásia-Pacífico: Singapura PDPA + Agentic AI Framework + Austrália Privacy Act** | 🟢 Planeado |
| **21** | **Certificações globais: ISO 42001:2023 (AIMS) + ISO 27001 full + ISO 27701 + SOC 2 Type II** | 🟢 Planeado |

## Funcionalidades principais

- **HDR Ledger** — registos imutáveis SHA-256 + RFC 3161 + TSA ICP-Brasil (Certisign/Serpro/FreeTSA)
- **Corpus Normativo** — validação pré-execução (LGPD, GDPR, …) com pesquisa FTS5
- **Pacote forense** — PDF/A-1/B + assinatura Ed25519
- **Soberania de modelos** — Ollama, OpenAI, Anthropic, custom
- **PWA mobile** — verificação, missões, evidências em campo
- **Docs Hub** — 10 documentos integrados
- **Onboarding** — tour guiado de 6 passos até ao primeiro HDR
- **Segurança** — JWT + cookies HttpOnly, rate limit (Redis + fallback), CSP/HSTS, structured logging JSON
- **Extração de texto** — PyMuPDF (PDF) + python-docx (DOCX) na ingestão de evidências
- **Conformidade** — página de relatório LGPD/GDPR com ancoragem constitucional + download PDF
- **Proxy cookie-aware** — Route Handler Next.js repassa cookies HttpOnly ao backend sem CORS

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

## Roadmap regulatório global

Ver análise completa em [`docs/ROADMAP-REGULATORIO.md`](docs/ROADMAP-REGULATORIO.md).

### 🇧🇷 Brasil

| Diploma | Obrigatoriedade | Fase |
|:---|:---|:---|
| LGPD — Lei 13.709/2018 | 🔴 Legal | 14 |
| Marco Civil — Lei 12.965/2014 | 🔴 Legal | 14 |
| ANPD Res. 15/2024 (incidentes 72h) | 🔴 Legal | 14 |
| MP 2.200-2/2001 (ICP-Brasil assinatura qualificada) | 🔴 Legal/Judicial | 15 |
| Lei 11.419/2006 (processo eletrônico) | 🔴 Legal/Judicial | 15 |
| CNJ Res. 615/2025 (IA no Judiciário) | 🟡 Mercado | 16 |
| OAB Rec. 001/2024 (IA na advocacia) | 🟡 Mercado | 16 |
| PL 2338/2023 (Marco Legal IA) | 🟡 Antecipação | 16 |

### 🇪🇺 União Europeia

| Diploma | Obrigatoriedade | Fase |
|:---|:---|:---|
| EU AI Act 2024/1689 — Alto Risco (prazo **ago/2026**) | 🔴 Legal (€35M / 7% global) | 17 |
| GDPR 2016/679 — utilizadores UE | 🔴 Legal (€20M / 4% global) | 17 |
| eIDAS 2.0 — Reg. 2024/1183 (QES + EUDI Wallet) | 🔴 Legal/Judicial | 17 |
| NIS2 — Diretiva 2022/2555 (cibersegurança) | 🟡 Mercado | 17 |

### 🇺🇸 Estados Unidos

| Diploma | Obrigatoriedade | Fase |
|:---|:---|:---|
| Colorado AI Act SB 205 (vigente **jun/2026**) | 🔴 Legal (Colorado) | 18 |
| CCPA/CPRA — utilizadores Califórnia | 🔴 Legal (California) | 18 |
| California SB 53 (jan/2026) | 🟡 Legal (California) | 18 |
| ABA Formal Opinion 512 (jul/2024) — Rules 1.1, 1.6, 5.3 | 🟡 Advocacia | 18 |
| NIST AI RMF 1.0 — boas práticas federais | 🟢 Enterprise | 18 |

### 🇦🇪 Emirados Árabes Unidos

| Diploma | Obrigatoriedade | Fase |
|:---|:---|:---|
| UAE PDPL — Decreto-Lei 45/2021 (AED 5M) | 🔴 Legal | 19 |
| DIFC Data Protection Law 5/2020 | 🔴 Legal (DIFC) | 19 |
| UAE AI Charter 2024 | 🟡 Mercado | 19 |
| Dubai AI Seal (contratos governamentais) | 🟡 Mercado | 19 |

### 🇬🇧 🇸🇬 🇦🇺 Outros mercados

| Diploma | Jurisdição | Fase |
|:---|:---|:---|
| UK GDPR + AI Code of Practice Regs 2026 | Reino Unido | 20 |
| PDPA + Agentic AI Framework (jan/2026) | Singapura | 20 |
| Privacy Act 1988 — automated decisions (dez/2026) | Austrália | 20 |
| Quebec Law 25 (mais rigorosa do Canadá) | Canadá | 20 |

### 🏅 Certificações internacionais

| Padrão | Cobertura | Fase |
|:---|:---|:---|
| ISO 42001:2023 — AI Management System (AIMS) | Global | 21 |
| ISO 27001:2022 — ISMS (certificação completa) | Global | 21 |
| ISO 27701:2019 — PIMS (privacidade) | Global | 21 |
| SOC 2 Type II — TSC (enterprise EUA/global) | EUA / Global | 21 |

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

# E2E (backend :8000 + frontend dev — ver docs/E2E-CI.md)
cd frontend
$env:BACKEND_PROXY_TARGET="http://127.0.0.1:8000"
npx playwright test --workers=1
```

Detalhes da pipeline e da jornada Playwright: [`docs/E2E-CI.md`](docs/E2E-CI.md).

## Segurança

- Next.js ≥ **15.4.10** (patches RSC — ver [blog Next.js](https://nextjs.org/blog/security-update-2025-12-11)).  
- Não commitar `.env` — ver auditoria Fase 12.  
- Rotas públicas de verificação: considerar WAF e limites adicionais em produção.  

## Licença e contacto

Projeto MVP Heillon / Estação Heillon — consulte a documentação em `docs/` para operação e conformidade LGPD.
