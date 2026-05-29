# Production Readiness — Heillon Legal (Beta Privado)

> **Documento vivo.** Atualizar a cada fase. Marca o estado real de prontidão
> para o **beta privado** (convites na segunda-feira). Itens marcados
> `⏸️ pós-CNPJ` são deliberadamente adiados até a liberação do CNPJ — não
> bloqueiam o beta.

Última revisão: Fase 30B4

---

## 1. Segurança & Auth

- [x] JWT em cookie HttpOnly (não localStorage)
- [x] Flags inseguras bloqueadas em produção (auth bypass, JWT default, rate limit)
- [x] Validação SSRF em `api_base_url` de agentes custom
- [x] Headers de segurança HTTP (`SecurityHeadersMiddleware`)
- [x] Rate limiting (middleware + Redis, race condition corrigida)
- [x] `/docs`, `/redoc`, `/openapi.json` fechados em produção
- [x] RLS PostgreSQL habilitado
- [x] Multi-key Fernet com rotação
- [x] Admin endpoints protegidos por `X-Heillon-Admin-Token` (503 sem token)
- [x] `.env` limpo do histórico git; `.env.example` documentado

## 2. Cadeia de Custódia (HDR)

- [x] HDR imutável: SHA-256 encadeado + Ed25519 + canonical_hash
- [x] Timestamp RFC 3161
- [x] `FORCE_STUB_TIMESTAMP=True` proibido em produção (RuntimeError no boot)
- [ ] ⏸️ pós-CNPJ — TSA ICP-Brasil real (Serpro/Certisign) com certificado A1
- [x] Verificação pública de HDR

## 3. Compliance LGPD

- [x] Centro de Privacidade `/privacy` (consentimento, RIPD, direitos do titular)
- [x] Solicitação de direitos ao DPO (prazo 15 dias)
- [x] **Auto-eliminação imediata** de conta (`DELETE /privacy/account`, art. 18 VI)
      — anonimiza, revoga chaves, **preserva HDRs** (valor probatório)
- [x] Retenção por tier + cron de purga (`scripts/cron_purge_retention.py`)
- [x] Banner de cookies (LGPD)
- [x] Templates: Política de Privacidade, Termos de Uso, DPIA/RIPD
- [x] Runbook de solicitação LGPD
- [ ] ⏸️ pós-CNPJ — preencher `[[PLACEHOLDER]]` legais (razão social, CNPJ, DPO nomeado)

## 4. Observability

- [x] Sentry opcional (no-op se DSN vazio; `send_default_pii=False`)
- [x] E-mail transacional Postmark com fallback stub
- [x] Structured logging
- [x] Painel admin `/admin` (métricas agregadas do beta, sem PII)
- [x] Health checks (`/health`)

## 5. Coletores (Substrato)

- [x] Browser Extension (Chrome MV3) — PoC
- [x] OpenAI Gateway (+ streaming SSE)
- [x] Anthropic Messages Gateway
- [x] Console standalone (ativo)

## 6. Infra & Deploy

- [x] Docker Compose (dev, prod, Caddy)
- [x] Caddyfile (TLS automático)
- [x] Backup PostgreSQL (`scripts/backup_postgres.sh`)
- [x] Bootstrap produção (`scripts/bootstrap_production.sh`)
- [x] CI/CD (ruff, mypy, pytest, postgres, security scan, corpus verify)
- [x] Deploy frontend (Vercel) + backend (Docker)
- [ ] ⏸️ pós-CNPJ — domínio definitivo + certificados de selo

## 7. Qualidade

- [x] Suíte backend verde (`pytest -q` — exit 0)
- [x] Build frontend verde (`npm run build`)
- [x] Typecheck frontend (`tsc --noEmit`)
- [x] Testes E2E (`frontend/tests/e2e/`)
- [x] Smoke script de beta (`scripts/beta_test.py` — 7 probes)

## 8. Lançamento do Beta

- [x] Manual do beta (`BETA.md`)
- [x] E-mail de convite (`INVITE_EMAIL.md`)
- [x] Guia de deploy (`DEPLOY.md`)
- [x] Tag `v0.1.0-beta`
- [ ] **Gate final pré-convite:** rodar smoke E2E contra ambiente live —
      `python scripts/beta_test.py --server https://<api-live> --api-key <chave>`
      (harness validado offline; precisa de URL/chave de produção)
- [ ] ⏸️ pós-CNPJ — precificação e selos de certificação

---

## Itens explicitamente adiados (pós-CNPJ)

Por decisão de produto, os itens abaixo **não bloqueiam o beta** e serão
tratados após a liberação do CNPJ (em andamento):

1. **Precificação** — planos e cobrança.
2. **CNPJ** — preenchimento de razão social / dados legais nos templates.
3. **Certificações de selo** — TSA ICP-Brasil real (Serpro/Certisign), certificado A1.

Durante o beta privado, o sistema opera com timestamp RFC 3161 e a cadeia de
custódia íntegra; os selos qualificados ICP-Brasil entram na sequência.
