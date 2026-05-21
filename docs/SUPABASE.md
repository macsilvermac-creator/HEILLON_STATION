# Supabase — Heillon Legal

## Situação

| Item | Estado |
|:---|:---|
| Schema Postgres no repo | `supabase/migrations/20260521120000_heillon_legal_schema.sql` |
| CLI local (`supabase init`) | Feito |
| Projeto na cloud | **`heillon-legal`** · ref `ydxjncqtsgikywfgfndx` · região `sa-east-1` |
| `supabase link` + `db push` | **Concluído** (schema aplicado) |
| Dashboard | https://supabase.com/dashboard/project/ydxjncqtsgikywfgfndx |
| Backend FastAPI a usar Postgres | **Próxima fase** — hoje o código usa **SQLite** (`sqlite3`) |

O agente **não tem** `SUPABASE_ACCESS_TOKEN` nesta máquina. Para criar o projeto na cloud, precisas de autenticar-te uma vez.

---

## 1. Login (uma vez)

```powershell
cd c:\HEILLON_STATION\heillon-legal
npx supabase login
```

Abre o browser e confirma com a conta Supabase (Google/GitHub/email).

---

## 2. Criar projeto na cloud

**Opção A — Dashboard**

1. [https://supabase.com/dashboard](https://supabase.com/dashboard) → **New project**
2. Nome sugerido: `heillon-legal`
3. Região: `South America (São Paulo)` se disponível
4. Guarda a **database password**

**Opção B — CLI** (após login)

```powershell
npx supabase projects create heillon-legal --org-id SEU_ORG_ID --db-password "SUA_SENHA_FORTE" --region sa-east-1
```

Lista orgs: `npx supabase orgs list`

---

## 3. Ligar o repo ao projeto

```powershell
cd c:\HEILLON_STATION\heillon-legal
npx supabase link --project-ref SEU_PROJECT_REF
```

O **Project ref** está em: Dashboard → Project Settings → General.

---

## 4. Aplicar o schema

```powershell
npx supabase db push
```

Ou cola o SQL de `supabase/migrations/20260521120000_heillon_legal_schema.sql` no **SQL Editor** do dashboard.

---

## 5. Variáveis para o backend (quando integrar Postgres)

No Supabase: **Project Settings → Database → Connection string → URI** (modo **Transaction** ou **Session**).

Cria `backend/.env`:

```env
DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

Para Vercel/Railway do API, usa o mesmo `DATABASE_URL` + **SSL**.

---

## 6. Próximo passo técnico (integração backend)

Para o FastAPI passar a usar Supabase de facto:

1. `psycopg[binary]` em `requirements.txt`
2. Camada de conexão Postgres em `app/db/` (substituir `sqlite3.Connection` nos repositórios)
3. Queries com placeholders `%s` e `INSERT ... ON CONFLICT`
4. Testes CI com Postgres local (`supabase start`) ou Testcontainers

Até lá, **SQLite local** continua a funcionar para desenvolvimento.

---

## Comandos úteis

```powershell
npx supabase status          # stack local (Docker)
npx supabase start           # Postgres local para dev
npx supabase db reset        # reaplica migrações locais
npx supabase projects list   # projetos na cloud (após login)
```
