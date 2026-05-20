# Heillon Legal — Legitimidade computacional para o Direito

**Versão MVP:** Maio de 2026 (Fases 1–3 concluídas) · **Backend:** 40 testes (`pytest`) · **Frontend:** `npm run build` OK  

O **Heillon Legal** é a vertical jurídica da **Estação Heillon**: cada passo relevante pode ser registado como **HDR** (Heillon Decision Record) — hash SHA-256, payload JSON **canónico** (RFC 8785 where aplicável), encadeamento criptográfico e carimbo **RFC 3161** (FreeTSA em produção, *stub* em testes).

## Ecossistema Heillon

| Recurso | URL |
|:---|:---|
| Sítio principal | [https://heillon.com](https://heillon.com) |
| Vitrine | [https://vitrine.heillon.com](https://vitrine.heillon.com) |
| Portal HDR | [https://hdr.heillon.com](https://hdr.heillon.com) |

## O que este repositório entrega

1. **Ingestão de evidências** — upload com hash consistente + HDR tipo `ingestion`
2. **Planeamento de missões** — mapeamento *keyword→agente* + **Corpus normativo** pré-execução
3. **Execução orquestrada** — DAG linear (MVP): um HDR encadeado por nó (**stubs**, sem IA real)
4. **Verificação pública** — `/verify/{hdr_id}` e `/verify/chain/{mission_id}`
5. **Pacote forense** — relatório executivo (**stub texto**, não PDF/A final), JSON da cadeia, manifesto, hash de integridade
6. **Diário de bordo** — listagem paginada, filtros e estatísticas agregadas
7. **Frontend Next.js** — modo missão, verificação, diário e ingestão, cliente em `frontend/lib/api.ts`

## Arquitetura do backend (DDD)

```
heillon-legal/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI + lifespan + routers dos domínios
│   │   ├── dependencies.py       # Depends() globais (DB, HDR…)
│   │   ├── core/                 # Infraestrutura partilhada (config, security, canonical_json)
│   │   ├── domain/
│   │   │   ├── hdr/              # Modelos HDR, HDRService, repositório, verificação, timestamp RFC3161
│   │   │   ├── evidence/         # Ingestão e armazenamento WORM
│   │   │   ├── mission/          # Orquestração, diário, repositório de missões, lexicon
│   │   │   ├── normative/       # Corpus normativo + regras públicas
│   │   │   └── forensic/        # Pacote forense + downloads
│   │   └── db/                   # SQLite, migrações
│   └── tests/
│       ├── conftest.py
│       ├── domain/               # Testes por bounded context (nomes únicos por ficheiro)
│       └── integration/
├── frontend/
│   ├── app/                     # Rotas Next.js App Router
│   ├── components/
│   └── lib/api.ts               # Cliente REST (NEXT_PUBLIC_BACKEND_URL)
└── docs/
    ├── CONTEXT.md
    └── API-REFERENCE.md
```

Consulte **`docs/API-REFERENCE.md`** para contratos REST alinhados ao código e **`docs/CONTEXT.md`** para o fluxo fim‑a‑fim.

## Stack técnico

| Camada | Ferramentas |
|:---|:---|
| API | FastAPI · Pydantic v2 · Uvicorn |
| Persistência | SQLite (ficheiros em `data/`) · migrações em `backend/app/db/migrations/` |
| Criptografia / integridade | SHA-256 (`generate_hdr_id`) · asn1crypto/httpx para RFC3161 |
| Frontend | Next.js 15 (**usar patch mínimo 15.4.10** — ver segurança) · Tailwind |
| Testes backend | pytest · Starlette TestClient |

> **Nota:** extensões tipo `sqlite-vss` podem constar na roadmap técnica; não fazem parte do `requirements.txt` actual.

## Arranque rápido · Backend

Requisitos: **Python ≥ 3.11** (recomendado 3.12).

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Estado: [`GET /health`](http://127.0.0.1:8000/health)

## Arranque rápido · Frontend

```powershell
cd frontend
npm install
# opcional:
# copy NUL .env.local  && echo NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000 >> .env.local
npm run build
npm run dev
```

Variável **`NEXT_PUBLIC_BACKEND_URL`**: por defeito o cliente usa `http://127.0.0.1:8000` (`frontend/lib/api.ts`). Ajuste se o backend correr doutra porta.

## Variáveis de ambiente (backend)

Definidas em `app/core/config.py` (ficheiro `.env` opcional).

| Variável | Descrição | Padrão |
|:---|:---|:---|
| `DATABASE_URL` | SQLite (`sqlite:///...`) | `sqlite:///./data/heillon.db` |
| `EVIDENCE_DIR` | Pasta das evidências ingeridas | `data/evidence` |
| `FORENSICS_PACKAGE_DIR` | Pasta dos pacotes forenses gerados | `data/forensic_packages` |
| `VERIFICATION_PUBLIC_BASE` | Base URL incluída no `verification_url` do manifesto (API pública HDR) | `http://127.0.0.1:8000` |
| `TSA_URL` | Autoridade de carimbo | `https://freetsa.org/tsr` |
| `FORCE_STUB_TIMESTAMP` | *Stub* RFC3161 determinístico (apenas dev/CI) | `false` |
| `API_V1_PREFIX` | Prefixo global da API versionada | `/api/v1` |
| `CORS_ORIGINS` | Lista de origins CORS JSON | por defeito inclui `http://localhost:3000` |

## Segurança · Next.js (App Router)

- A linha **15.4.x** deve usar pelo menos **`next@15.4.10`**, que corrige **CVE-2025-55183** (exposição de código compilado via RSC), **CVE-2025-55184**/**CVE-2025-67779** (DoS no protocolo RSC) além do ciclo anterior em torno de **CVE-2025-66478** / React2Shell. Ver o comunicado oficial: [Security Update December 11, 2025](https://nextjs.org/blog/security-update-2025-12-11) e o tooling [`npx fix-react2shell-next`](https://github.com/vercel-labs/fix-react2shell-next).
- Estratégia recomendada: manter **`next`** e **`eslint-config-next`** na **mesma versão patched** dentro da série em uso (`npm install next@15.4.10 eslint-config-next@15.4.10`), voltar a correr **`npm audit`**, **`npm run build`** e regressões manuais nas páginas App Router.

## Endpoints principais (resumo)

| Método | Caminho | Descrição |
|:---|:---|:---|
| `GET` | `/health` | Liveness |
| `POST` | `/api/v1/ingestion` | Upload de evidência (+ HDR ingestion) |
| `GET` | `/api/v1/verify/{hdr_id}` | Verificar um HDR |
| `GET` | `/api/v1/verify/chain/{mission_id}` | Verificar cadeia por `mission_id` |
| `POST` | `/api/v1/mission/plan` | Planear missão |
| `POST` | `/api/v1/mission/{id}/approve` | Aprovar |
| `POST` | `/api/v1/mission/{id}/execute` | Executar DAG aprovado |
| `GET` | `/api/v1/mission/diary` | Diário com filtros |
| `GET` | `/api/v1/mission/diary/stats` | Estatísticas |
| `GET` | `/api/v1/normative/rules` | Corpus activo |
| `POST` | `/api/v1/forensic/package/{mission_id}` | Gerar pacote (missão **completed**) |
| `GET` | `/api/v1/forensic/package/{package_id}` | Metadados do pacote |
| `GET` | `/api/v1/forensic/package/{package_id}/download/pdf` | Relatório executivo (**stub `.txt`**) |
| `GET` | `/api/v1/forensic/package/{package_id}/download/json` | JSON da linhagem HDR |
| `GET` | `/api/v1/forensic/package/{package_id}/download/manifest` | Manifesto JSON |

## Roadmap próximo

- Agentes de IA reais / workers de produção
- PDF/A final + assinaturas jurídicas fortes
- Autenticação, multi‑tenant e *hardening* operacional (WAF / limites nas rotas públicas Verificação)
- Integração Postgres e políticas de arquivo
