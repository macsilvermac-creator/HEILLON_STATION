# Heillon Legal — Browser Extension (MV3)

> Coletor invisível de interações com IA jurídica.
> Captura ChatGPT, Claude e Gemini → gera HDR criptográfico no substrato Heillon.

**Versão:** 0.1.0 · **Manifest:** v3 · **Browsers:** Chrome 114+, Edge, Brave

---

## O que faz

1. Observa silenciosamente o uso de IA generativa em domínios explicitamente listados
   (ChatGPT, Claude, Gemini).
2. Quando uma resposta termina de streamear, envia `{prompt, response, model, source_url}`
   para `POST /api/v1/extension/capture` no servidor Heillon configurado.
3. O servidor gera um HDR (Heillon Detailed Record) assinado com selo ICP-Brasil
   qualificado, encadeado por SHA-256 ao registo anterior — defensável em juízo.
4. Mostra um toast discreto `✓ Auditado` com link para verificação pública.

**Princípios:**
- Captura **só** os 3 domínios listados em `manifest.json:host_permissions`. Nenhum outro.
- API key e config ficam **apenas neste dispositivo** (`chrome.storage.local`, nunca sync).
- Provedor pode ser desligado por opt-out na página de Opções.
- Toda saída de rede vai **só** para o servidor Heillon configurado.

---

## Instalação (desenvolvimento)

1. `git clone` este repo.
2. Em Chrome, abra `chrome://extensions`.
3. Ative **Modo Desenvolvedor** (canto superior direito).
4. Clique **Carregar sem compactação** e selecione a pasta `extension/`.
5. Abra **Opções** da extensão (clique no ícone do quebra-cabeça → Heillon → Opções).
6. Preencha:
   - **URL do servidor:** `http://127.0.0.1:8000` (dev) ou seu deployment.
   - **Chave de API:** gere em `Console → Conta → Chaves de API` (formato `heillon_live_…`).
7. Clique **Salvar e testar**. Status deve ficar verde com plano + quota.

---

## Arquitetura

```
extension/
├── manifest.json                    # MV3, host_permissions whitelisted, minimal perms
├── icons/                           # 16, 48, 128 px
└── src/
    ├── background/
    │   └── sw.js                    # service worker — handles capture msgs, quota refresh, badge
    ├── content/
    │   ├── notifier.js              # toast (Shadow DOM, no CSS collision)
    │   └── adapters/
    │       ├── chatgpt.js           # ChatGPT DOM observer + Q→A pairing
    │       ├── claude.js            # Claude adapter
    │       └── gemini.js            # Gemini adapter
    ├── popup/                       # 360×400 popup (status, quota, last 5 HDRs)
    │   ├── popup.html
    │   ├── popup.css
    │   └── popup.js
    ├── options/                     # full options page (API key, provider opt-in, metrics)
    │   ├── options.html
    │   ├── options.css
    │   └── options.js
    └── shared/
        ├── constants.js             # endpoints, storage keys, defaults
        ├── storage.js               # async chrome.storage.local wrappers
        └── api.js                   # HTTP client with timeout + structured error
```

**Permissões declaradas (e por quê):**
- `storage` — armazena API key, settings, métricas locais.
- `alarms` — refresh periódico da quota (a cada 15 min).
- `host_permissions` — limitado a 3 domínios IA. **Nada de `<all_urls>`**.

**O que NÃO usamos (intencionalmente):**
- `tabs` (não precisamos enumerar abas).
- `webRequest` (MV3 não permite ler bodies; usamos DOM observation).
- `cookies` (auth via API key, não cookie).
- `scripting` injection dinâmica (content scripts já declarados em manifest).

---

## Endpoints consumidos

| Método | Path | Quando |
|---|---|---|
| GET | `/api/v1/extension/health` | Validar API key + obter quota (alarme 15min + popup) |
| POST | `/api/v1/extension/capture` | A cada Q→A detectado |

**Auth:** header `X-Heillon-Api-Key: heillon_live_…`
**Sem cookies, sem credentials. CORS regex aceita `chrome-extension://[a-z]{32}`.**

**Códigos de resposta esperados:**
- `201` — captura aceita, HDR gerado
- `401` — chave inválida ou revogada
- `402` — quota mensal atingida (free=50)
- `422` — payload inválido (prompt > 64k, response > 256k, provider desconhecido)
- `5xx` — erro server-side; extensão mostra toast vermelho

---

## Privacidade & LGPD

Ver [PRIVACY.md](./PRIVACY.md).

---

## Roadmap

- [x] PoC capturando ChatGPT/Claude/Gemini
- [x] Auth via API key, quota enforcement, badge dinâmico
- [x] Popup + Options + métricas locais
- [ ] Empacotamento `.zip` para Chrome Web Store
- [ ] Submissão Edge Add-ons Store
- [ ] Adapter para Mistral, DeepSeek, Perplexity (sob demanda)
- [ ] Firefox port (Manifest V3 com diferenças de service worker)
