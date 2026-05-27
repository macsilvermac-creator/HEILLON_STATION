# Deploy do Heillon Legal — Frontend (Vercel) + Backend (Docker)

## Frontend — Vercel

### Por que existe `package.json` na raiz?

O Heillon Legal é estruturado como monorepo: o Next.js vive em `frontend/`, e
o backend Python em `backend/`. A Vercel, por padrão, procura o `package.json`
da raiz do repositório para detectar o framework — sem essa declaração, dá o
erro:

```
Error: No Next.js version detected.
```

Para resolver sem mudanças na UI da Vercel, declaramos `next` no
`package.json` da raiz **somente para satisfazer o detector de framework**.
O `vercel.json` então usa `installCommand` apontando para `frontend/` para
instalar de verdade e fazer o build correto.

### Opção limpa (recomendada longo prazo)

Para evitar o `package.json` na raiz de propósito-único:

1. Acesse o projeto na Vercel (`vercel.com/dashboard`).
2. Vá em **Settings → General**.
3. Em **Root Directory**, defina: `frontend`
4. Clique **Save**.
5. Re-deploy.

Quando o Root Directory está configurado na UI, a Vercel olha apenas a
subpasta `frontend/` — então:

- O `vercel.json` da raiz **pode ser apagado** (ou movido para
  `frontend/vercel.json` se houver config Vercel-específica).
- O `package.json` da raiz pode ser **simplificado para não declarar `next`**
  (ou apagado se não houver scripts úteis).
- A Vercel acha `frontend/package.json` automaticamente.

### Re-deploy após este commit

Depois do commit que adicionou o `package.json` da raiz + `vercel.json`
atualizado, o redeploy deve correr sem o erro. Se ainda falhar:

1. Confirme que o último commit está na branch `main`.
2. Force redeploy pela Vercel: **Deployments → ... → Redeploy**.
3. Marque **"Use existing Build Cache"** como **off** (cache pode estar com
   estado antigo).

### Variáveis de ambiente necessárias (Vercel)

| Variável | Valor exemplo | Notas |
|---|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `https://api.heillon.com` | URL pública do backend |
| `BACKEND_PROXY_TARGET` | `https://api.heillon.com` | Para Route Handler proxy |
| `NEXT_PUBLIC_SITE_URL` | `https://heillon-legal-ui.vercel.app` | Usada por robots.ts / sitemap.ts |
| `NEXT_PUBLIC_PLANS_URL` | `https://heillon.com/planos` | CTA do banner Free |
| `NEXT_PUBLIC_CHROME_EXTENSION_URL` | (Chrome Web Store URL) | Link do onboarding |

---

## Backend — Docker → VPS

Ver `Dockerfile`, `docker-compose.yml` e `.github/workflows/deploy.yml`.

Pipeline automático:
1. Push em `main` → CI roda (`.github/workflows/ci.yml`)
2. Após CI passar → `deploy.yml` faz build da imagem Docker e push para `ghcr.io`
3. SSH para VPS → `docker compose pull backend && docker compose up -d backend`
4. Health check em `http://localhost:8000/health`

### Segredos no GitHub Repository (Settings → Secrets)

| Segredo | Função |
|---|---|
| `DEPLOY_HOST` | hostname/IP do VPS |
| `DEPLOY_USER` | usuário SSH |
| `DEPLOY_SSH_KEY` | chave privada SSH |
| `DEPLOY_PORT` | porta SSH (default 22) |
| `GHCR_PAT` | (opcional) PAT para pull de ghcr.io |
| `VERCEL_TOKEN` | token Vercel para deploy frontend |
| `VERCEL_ORG_ID` | ID da organização Vercel |
| `VERCEL_PROJECT_ID` | ID do projeto Vercel |

### Variáveis de ambiente no VPS (docker-compose)

| Variável | Obrigatória | Notas |
|---|---|---|
| `POSTGRES_PASSWORD` | ✅ | docker-compose.yml falha sem |
| `AUTH_SECRET_KEY` | ✅ | mín. 32 chars; falha sem |
| `FERNET_ENCRYPTION_KEY` | ✅ | gerar com `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `FERNET_ENCRYPTION_KEY_LEGACY` | (opcional) | Lista CSV de chaves antigas durante rotação (ver Fase 24B) |
| `BILLING_WEBHOOK_SECRET` | (opcional) | HMAC-SHA256 para webhook do site de marketing |
| `VERIFICATION_PUBLIC_BASE` | recomendado | URL pública do backend (para selos verificáveis) |
