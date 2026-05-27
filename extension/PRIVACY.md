# Política de Privacidade — Heillon Legal Browser Extension

**Última atualização:** 27 de maio de 2026
**Versão da extensão:** 0.1.0
**Controlador de dados:** Heillon Legal
**Encarregado de Dados (DPO):** dpo@heillon.com

---

## 1. Resumo em uma frase

A extensão captura suas conversas com ChatGPT, Claude e Gemini e envia para o
servidor Heillon que você configurou. Nada mais. Nada para outros lugares.

---

## 2. Dados coletados

A extensão coleta, **apenas durante o uso ativo dos provedores listados:**

| Dado | Origem | Uso |
|---|---|---|
| **Prompt** (texto enviado à IA) | DOM da página | Gera HDR no servidor configurado |
| **Response** (resposta da IA) | DOM da página | Gera HDR no servidor configurado |
| **Provider** (openai/anthropic/google) | URL da página | Categoriza o HDR |
| **Model** (gpt-4o, claude-3.5, etc.) | DOM (selector do modelo) | Metadado do HDR |
| **Source URL** | `location.href` | Vinculada ao HDR para auditoria |
| **AI session ID** | URL path (`/c/{uuid}`) | Agrupa capturas da mesma conversa |
| **Page title** | `document.title` | Identificação visual no console |
| **Captured at** | `Date.now()` no browser | Timestamp local |

**A extensão NÃO coleta:**
- Histórico de navegação em outros sites
- Cookies, localStorage, sessionStorage de qualquer site
- Senhas, dados de cartão, dados de formulários não-IA
- Identificação do dispositivo (user agent, IP — esses só são vistos pelo
  servidor Heillon ao receber o POST, não pela extensão)

---

## 3. Onde os dados vão

**Apenas para o servidor Heillon que VOCÊ configurar** nas Opções da extensão.

- Configuração padrão: `http://127.0.0.1:8000` (seu próprio servidor de desenvolvimento)
- Em produção, tipicamente: domínio da sua organização ou `https://api.heillon.com`

**Nenhum dado é enviado para a Heillon Legal por padrão.** Você controla o destino.

A extensão **NÃO** envia telemetria para Heillon Legal, Google, ou qualquer
terceiro. Verificação: inspecione `src/shared/api.js` — o único `fetch()` da
extensão usa o `serverUrl` definido pelo usuário.

---

## 4. Onde os dados ficam no dispositivo

`chrome.storage.local` apenas. **Nunca** `chrome.storage.sync` (que replicaria
para outros dispositivos via conta Google).

Itens armazenados:
- `heillon_api_key` — sua chave (formato `heillon_live_…`)
- `heillon_server_url` — URL do servidor configurado
- `heillon_enabled_providers` — quais provedores estão ativos
- `heillon_last_quota` — snapshot da quota (apenas números, sem PII)
- `heillon_recent_hdrs` — últimos 20 IDs de HDR (apenas IDs + URLs, sem texto)
- `heillon_metrics` — contadores locais de capturas e erros

Para apagar tudo: `chrome://extensions` → Heillon → **Remover**.

---

## 5. Bases legais (LGPD)

| Base legal | Aplicação |
|---|---|
| **Art. 7º I LGPD — Consentimento** | Você instalou a extensão voluntariamente e configurou os domínios capturados |
| **Art. 7º V LGPD — Execução de contrato** | Captura é o objeto do serviço contratado com o operador do servidor Heillon |
| **Art. 7º VI LGPD — Exercício regular de direitos em processo judicial** | HDRs servem como prova em juízo de uso responsável de IA |

---

## 6. Seus direitos

Para dados **armazenados localmente** (na extensão): vá a Opções → desinstale a
extensão. Tudo apagado.

Para dados **enviados ao servidor Heillon**: exerça seus direitos LGPD (acesso,
correção, eliminação, portabilidade) diretamente no servidor configurado:

- Console: `<server_url>/privacy`
- Email do DPO: definido em `<server_url>/api/v1/privacy/dpo` (varia por organização)

---

## 7. Segurança

- API key armazenada com criptografia do sistema operacional (chrome.storage.local
  herda do User Profile do Chrome — Windows DPAPI / macOS Keychain / Linux libsecret).
- Conexão com servidor: HTTPS recomendado em produção. HTTP só para `127.0.0.1` dev.
- API keys são revogáveis a qualquer momento no console (`/conta/api-keys`).

---

## 8. Transferência internacional

A extensão em si não transfere dados — ela apenas envia ao servidor que você
configurou. Se esse servidor estiver em outro país, a transferência internacional
fica sob responsabilidade do operador do servidor (não da extensão).

---

## 9. Retenção

A extensão **não retém** prompts/respostas localmente além do necessário para
enviar ao servidor. Após o envio bem-sucedido, o conteúdo só fica no servidor
(sujeito à política de retenção do servidor — tipicamente 30d no plano Free,
365d no Pro, 5 anos no Team, indefinido no Enterprise).

Apenas os IDs dos últimos 20 HDRs ficam em cache local (para exibição no popup).

---

## 10. Atualizações desta política

Mudanças materiais serão comunicadas via release notes da extensão na Chrome
Web Store. A versão atual sempre está em `extension/PRIVACY.md` no repositório
público.

---

**Contato:** dpo@heillon.com
**Repositório:** https://github.com/heillon/heillon-legal (público para auditoria)
