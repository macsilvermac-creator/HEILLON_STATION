# E2E e CI — Heillon Legal

## Estratégia (estabilidade + segurança)

| Camada | O quê valida | Porquê |
|:---|:---|:---|
| **pytest** (`backend`) | Regras de negócio, HDR, normativa, Postgres | Rápido, determinístico, sem browser |
| **npm run build** | Frontend compila (29 rotas) | Falhas de tipo/SSR |
| **Playwright smoke** | `/docs`, `/login` | Páginas estáticas, sem backend |
| **Playwright jornada** | Registo UI + API via **proxy Next** + verificação + LGPD + docs | Mesmo caminho que o utilizador (cookies, `/api/v1` same-origin) |
| **Job `backend-postgres`** | Bootstrap schema Supabase no Postgres 16 | Postgres não bloqueia E2E |

### Princípios

1. **API E2E através de `page.request`** com URLs `/api/v1/...` (porta 3000), não chamadas directas à :8000 — valida proxy, CORS e cookies.
2. **Sessão híbrida (cookie + bearer)** — cookie HttpOnly para XSS; bearer em `localStorage` mantido após `/auth/me` para proxy dev/CI e clientes API. O proxy Next nem sempre reencaminha `Set-Cookie` do backend.
3. **SQLite no job E2E** — isolado em `/tmp/heillon_e2e.db`; sem dados de produção.
4. **Rate limit desligado só com `CI_E2E=true`** — evita 429 em pipelines; produção mantém Redis/memória.
5. **Segredos** — `AUTH_SECRET_KEY` apenas em GitHub Secrets / `.env` local (nunca no repo).

## Executar localmente

```powershell
# Terminal 1 — backend
cd backend
$env:CI_E2E="true"
$env:FORCE_STUB_TIMESTAMP="true"
$env:ENVIRONMENT="development"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — E2E
cd frontend
$env:BACKEND_PROXY_TARGET="http://127.0.0.1:8000"
$env:NEXT_PUBLIC_BACKEND_URL="http://127.0.0.1:8000"
npx playwright test --workers=1
```

## Ficheiros

- `frontend/tests/e2e/helpers/heillon-api.ts` — helpers com mensagens de erro claras
- `frontend/tests/e2e/smoke.spec.ts` — smoke UI
- `frontend/tests/e2e/full-journey.spec.ts` — jornada completa
- `.github/workflows/ci.yml` — pipeline
