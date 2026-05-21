# Vercel — configurar projeto com CLI (Heillon Legal)

O frontend é **Next.js** em **`frontend/`**. O backend **FastAPI** não corre na Vercel; só precisa de uma URL HTTPS acessível (Railway, Render, Fly.io, VPS, etc.).

## Porque o login pode falhar “sozinho”

`npx vercel login` ou `vercel whoami` abrem **OAuth por dispositivo** (abra o URL no browser e confirme). Em ambientes automatizados use um **Personal Access Token** em [Tokens da conta · Vercel](https://vercel.com/account/tokens) — variável **`VERCEL_TOKEN`**.

---

## Passo rápido (script)

Na raiz do repositório (pasta **`heillon-legal`**):

```powershell
.\scripts\bootstrap-vercel.ps1 `
  -VercelToken "SEU_TOKEN" `
  -ProjectName "heillon-station-frontend" `
  -BackendPublicUrl "https://sua-api.exemplo.com" `
  -Team "seu-time-ou-org"   # opcional; Hobby costuma estar vazio
```

O script (quando há backend URL):

1. Associa **`frontend`** ao projeto (`vercel link`).
2. Liga o Git **`https://github.com/macsilvermac-creator/HEILLON_STATION.git`** (`vercel git connect`).
3. Define variáveis de produção **`BACKEND_PROXY_TARGET`** e **`INTERNAL_API_ORIGIN`** (iguais ao URL público HTTPS da API, sem `/` extra no fim recomendável).

Repõe só o comando se alterares projeto ou scopes.

---

## Obrigatório no Dashboard (monorepo)

Com o repositório Git completo (**backend + frontend** na raiz), a Vercel faz clone de **todo** o repo. É preciso:

**Settings → General → Root Directory → `frontend`**

 Sem isto, o build aponta para a raiz e falha ou compila projeto errado.

---

## Fluxo manual (equivalente ao script)

Na pasta **`frontend`**:

```powershell
cd frontend
npx vercel login
```

Criar / ligar projeto:

```powershell
npx vercel link --yes --project heillon-station-frontend
# Time (team scope):
# npx vercel link --yes -S SUA_ORG --project heillon-station-frontend
```

Ligar o GitHub já existente:

```powershell
npx vercel git connect https://github.com/macsilvermac-creator/HEILLON_STATION.git
```

Variáveis (produção; repetir **`preview`** se quiseres PRs funcionais contra a mesma API):

```powershell
npx vercel env add BACKEND_PROXY_TARGET production --value "https://sua-api.exemplo.com" --yes --no-sensitive
npx vercel env add INTERNAL_API_ORIGIN production --value "https://sua-api.exemplo.com" --yes --no-sensitive
```

Deploy manual:

```powershell
npx vercel deploy --prod
```

Após configurar **`Root Directory = frontend`** e variáveis, cada **`git push`** na branch ligada faz redeploy automaticamente.

---

## CORS no backend

Na API FastAPI (`CORS_ORIGINS`), inclui o domínio Vercel (`https://….vercel.app`) e mais tarde o domínio próprio.

---

## Referência de variáveis (Next deste repo)

| Variável | Onde usar |
|---------|-----------|
| `BACKEND_PROXY_TARGET` | **Build/deploy** — rewrites `/api/v1/*` → FastAPI (`next.config.ts`). |
| `INTERNAL_API_ORIGIN` | SSR / Node — mesmo URL da API quando `NEXT_PUBLIC_BACKEND_URL` não serve (`frontend/lib/api.ts`). |

Opcional: `NEXT_PUBLIC_BACKEND_URL` apenas se algum fluxo precisar de URL absoluta também no cliente (o browser usa já same-origin `/api/v1/` com o proxy).
