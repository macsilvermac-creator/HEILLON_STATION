# Auditoria de segredos — Fase 12

**Data:** Maio 2026  
**Âmbito:** `heillon-legal` (backend, frontend, CI, repositório Git)

## Resumo

| Item | Estado | Notas |
|:---|:---|:---|
| `.env` no `.gitignore` | OK | Raiz e `frontend/` |
| `backend/.env` commitado | OK | Não encontrado no índice Git |
| `AUTH_SECRET_KEY` default | AVISO | Valor `dev-insecure-heillon-secret-change-in-production-…` — apenas desenvolvimento |
| `FERNET_ENCRYPTION_KEY` | OK | Obrigatório em `ENVIRONMENT=production`; derivado em dev |
| `frontend/.env.local.example` | OK | Apenas placeholders (`NEXT_PUBLIC_BACKEND_URL`) |
| Tokens Supabase no chat | AÇÃO | Revogar token `sbp_…` exposto em conversa anterior |
| `OPENAI_API_KEY` em código | OK | Apenas via variável de ambiente |
| `POSTGRES_PASSWORD` em docker-compose | AVISO | Default `changeme` — substituir em produção |

## `backend/app/core/config.py`

- Segredos carregados de ambiente / `.env` (não versionado).
- `AUTH_SECRET_KEY` tem default longo marcado implicitamente como dev-only pelo nome.
- Produção exige `FERNET_ENCRYPTION_KEY` explícita e distinta do JWT.

## Recomendações

1. Nunca commitar `backend/.env`, `frontend/.env.local`, nem chaves Ed25519 hex.
2. GitHub Actions: definir `AUTH_SECRET_KEY`, `FERNET_ENCRYPTION_KEY`, `POSTGRES_PASSWORD` como **Secrets**.
3. Vercel: `NEXT_PUBLIC_BACKEND_URL` + `BACKEND_PROXY_TARGET` para API real.
4. Supabase: password só no dashboard / secret manager — não no repositório.

## Verificação manual

```powershell
git ls-files | Select-String -Pattern '\.env'
rg -n "sk-|sbp_|password\s*=\s*['\"][^'\"]+['\"]" heillon-legal --glob '!*.md'
```
