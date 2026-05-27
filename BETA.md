# Heillon Legal — Programa Beta Privado

> **Você é um dos primeiros operadores reais a testar o Heillon Legal.**
> Este manual te leva de zero ao primeiro registo auditado de IA em
> ~5 minutos, e depois te guia por 5 cenários que validam toda a promessa.

---

## 🎯 Por que você está aqui

Heillon Legal é o **substrato de auditoria forense de IA jurídica**. Sempre
que você (ou sua equipe) usa ChatGPT, Claude ou Gemini para tarefas legais,
o Heillon gera silenciosamente um **HDR (Heillon Detailed Record)** — um
registro criptograficamente selado, assinado com timestamp ICP-Brasil, que
prova em juízo (ou auditoria) que aquela IA foi usada com:

- ✓ Cadeia de custódia íntegra (SHA-256 encadeado)
- ✓ Selo de tempo qualificado (RFC 3161 + ICP-Brasil)
- ✓ Validação contra corpus normativo brasileiro (LGPD, CNJ 615, OAB 001,
  CPC, CPP, CLT, Marco Civil) + internacional (GDPR, EU AI Act, ISO 42001)
- ✓ Verificação pública sem login (link compartilhável)

**Frase-moat:** *Cadeia de custódia de IA jurídica que vale em juízo.
Invisível no uso. Inevitável em auditoria.*

---

## 🚀 Setup em 5 minutos

### 1. Credenciais (1 minuto)

Você recebeu:
- **URL do servidor**: ex. `https://api.heillon-beta.com` ou
  `http://127.0.0.1:8000` (se estiver rodando local).
- **Chave de API**: começa com `heillon_live_...`

> Não tem? Solicite em: dpo@heillon.com (com CC para quem te convidou)

### 2. Console web (1 minuto)

Abra `https://<seu-servidor>/conta/quota` e faça login. Confirme:

- Plano: **Free** (50 HDRs/mês)
- Quota: **0/50 HDRs neste período**
- Acesse `/conta/api-keys` — sua chave deve estar lá.

### 3. Browser Extension (2 minutos)

A extensão captura ChatGPT/Claude/Gemini invisivelmente. Para o beta:

1. Em Chrome, vá em `chrome://extensions`
2. Ative **Modo Desenvolvedor** (canto superior direito)
3. Clique **Carregar sem compactação** → selecione a pasta `extension/`
4. Clique no ícone Heillon (canto do browser) → **Opções**
5. Preencha **URL do servidor** + **Chave de API** → **Salvar e testar**

Aparece "✅ Conectado · plano Free · 0/50 HDRs"? Setup OK.

### 4. Validação automática (1 minuto)

Rode o script de validação:

```bash
cd scripts/
python beta_test.py \
  --server https://<seu-servidor> \
  --api-key heillon_live_<sua-chave>
```

7 testes automatizados rodam em ~10 segundos. Ao final, ele gera um
arquivo `beta_test_report_<data>.json` — anexe este arquivo no seu
feedback ao final do beta.

---

## 🧪 Os 5 cenários (faça pelo menos 3)

Cada cenário valida UMA promessa do Heillon. Marque sua experiência em
cada um — esse é o material que mais nos ajuda.

### Cenário 1 — Captura automática invisível (5 min) · **OBRIGATÓRIO**

**Promessa testada:** Você usa IA normalmente, Heillon audita sem fricção.

1. Com a extensão ativa, abra `https://chat.openai.com`
2. Faça uma pergunta jurídica real (ex: "Resuma o art. 7º da LGPD")
3. Aguarde a resposta completa
4. Veja o canto inferior direito da tela:
   - ✓ Apareceu o toast **"✓ Auditado"** com link?
   - ✓ Clicou no link e abriu uma página `/verification/<hdr_id>`?
5. Repita com `https://claude.ai` e `https://gemini.google.com`

**Avalie:**
- 🟢 Funcionou em todos os 3 sites? (0–10)
- 🟢 O toast incomodou seu trabalho? (deveria ser 0)
- 🟢 Você confiaria no que viu como prova em juízo? (justifique)

---

### Cenário 2 — Verificação pública (3 min)

**Promessa testada:** Qualquer pessoa (juiz, perito, advogado contrário)
verifica o HDR sem login.

1. Pegue um HDR criado no Cenário 1 (no popup da extensão, clique
   em um registro recente — copia o link de verificação)
2. Abra esse link em uma **janela anônima** (sem login)
3. Confirme que aparece:
   - O hash canônico (SHA-256)
   - O timestamp qualificado
   - A cadeia de custódia (HDRs encadeados)
   - O resultado da validação normativa

**Avalie:**
- 🟢 Compreensível para alguém sem treinamento técnico? (0–10)
- 🟢 Linguagem jurídica adequada? (não cripto)
- 🟢 Você apresentaria isso em juízo? (justifique)

---

### Cenário 3 — Cota e upgrade (5 min)

**Promessa testada:** Free tem 50 HDRs/mês; o sistema avisa antes e
bloqueia educadamente ao atingir.

1. No console (`/conta/quota`), confirme uso atual.
2. **Não dá pra testar o limite real sem queimar 50 HDRs.** Em vez disso:
   - Veja o banner do plano Free no topo do console (aparece quando uso ≥ 70%)
   - Clique em "Ver planos" → deve abrir o site externo de marketing
   - Volte ao console e dispense o banner — confirma que ele some por 24h

**Avalie:**
- 🟢 Banner intrusivo? (deveria ser não)
- 🟢 CTA pra planos pago é claro?
- 🟢 Você upgrade-aria por quanto? (preço sweet-spot)

---

### Cenário 4 — MCP Gateway com API existente (10 min) · **TÉCNICO**

**Promessa testada:** Troca **1 URL** no seu código Python existente
que usa OpenAI/Anthropic e tudo passa a ser auditado.

Tem código Python rodando OpenAI ou Anthropic? Troque o `base_url`:

```python
# ANTES — chamada direta OpenAI
from openai import OpenAI
client = OpenAI(api_key="sk-...")

# DEPOIS — passando pelo Heillon Gateway
client = OpenAI(
    base_url="https://<seu-servidor>/api/v1/gateway",
    api_key="heillon_live_<sua-chave>",
    default_headers={"X-Upstream-Api-Key": "sk-..."},
)

# Resto do código IDÊNTICO:
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Resuma art. 7 LGPD"}],
)
print(response.choices[0].message.content)

# Bonus: o response.headers tem X-Heillon-Hdr-Id com o ID do HDR criado
```

Para Anthropic SDK nativo:

```python
import anthropic
client = anthropic.Anthropic(
    base_url="https://<seu-servidor>/api/v1/gateway/anthropic",
    api_key="heillon_live_<sua-chave>",
    default_headers={"X-Upstream-Api-Key": "sk-ant-..."},
)
msg = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=512,
    messages=[{"role": "user", "content": "Resuma art. 7 LGPD"}],
)
```

**Avalie:**
- 🟢 Latência aceitável? (deveria adicionar < 200ms p/ overhead)
- 🟢 Quebrou algo no seu app? (lista os problemas)
- 🟢 LangChain/LlamaIndex/Cursor funcionou sem mudança extra?

---

### Cenário 5 — Streaming (5 min) · **TÉCNICO**

**Promessa testada:** Streaming funciona (LangChain agents, chat UIs)
sem perder a auditoria.

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://<seu-servidor>/api/v1/gateway",
    api_key="heillon_live_<sua-chave>",
    default_headers={"X-Upstream-Api-Key": "sk-..."},
)

stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Conte uma história curta sobre IA jurídica"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

**Avalie:**
- 🟢 Stream veio chunk-a-chunk como sempre? (latência primeiro token)
- 🟢 Após o stream, o HDR apareceu no `/conta/quota` ou `/missions`?
- 🟢 Você reusaria isso na sua produção?

---

## 🎯 O que observar — sinais de valor

Durante os cenários, fique atento a esses momentos:

| Momento | O que você sente? |
|---|---|
| ✨ Toast "✓ Auditado" aparece sem você fazer nada | "Não atrapalha" / "Esqueço que existe" |
| ✨ Link de verificação abre página clara em janela anônima | "Posso mandar isso para um juiz" |
| ✨ Quota usada aparece no popup da extensão | "Tenho controle do que está sendo capturado" |
| ✨ Gateway adiciona < 200ms à sua chamada IA | "Não preciso mudar minha arquitetura" |
| ✨ Streaming continua chunk-a-chunk com Heillon no meio | "Funciona com meu agente LangChain" |

Se esses momentos NÃO aconteceram com você, **isso é o feedback mais
valioso** — significa que a promessa não está sendo cumprida ainda.

---

## 🐛 O que NÃO funcionar = informação valiosa

Quebrou algo? **Ótimo, é exatamente o que estamos procurando.** Anote:

- **O que você fez** (URL, ação, payload)
- **O que esperava ver** (toast, HDR, response)
- **O que viu** (erro, comportamento estranho, silêncio)
- **Stack trace ou screenshot** se aplicável

Anexe ao seu relatório no `FEEDBACK.md`.

---

## ❓ FAQ

**P: Posso usar a extensão em produção / com clientes reais durante o beta?**
R: Sim, mas saiba que o tier Free apaga HDRs após 30 dias. Para retenção
maior, faça upgrade ou só use a partir do GA.

**P: A extensão captura emails / outras coisas além de ChatGPT/Claude/Gemini?**
R: Não. `manifest.json` lista exatamente os 4 hostnames (chat.openai.com,
chatgpt.com, claude.ai, gemini.google.com). Você pode auditar o código
aberto.

**P: Onde vão meus prompts e respostas?**
R: Apenas para o servidor Heillon que VOCÊ configurou. Sem telemetria
para Heillon Legal. Detalhes em `extension/PRIVACY.md`.

**P: Posso opt-out de um provedor?**
R: Sim — extensão → Opções → desmarque o provedor (OpenAI/Anthropic/Google).

**P: O sistema funciona se meu backend Heillon estiver caído?**
R: A extensão sinaliza erro mas NÃO bloqueia sua interação com a IA.
Você continua trabalhando; só não terá HDR daquela conversa.

**P: Quanto tempo o beta dura?**
R: 30 dias a partir da sua ativação. Receberá email para feedback estruturado
no dia 14 e no dia 30.

---

## 📮 Como dar feedback

1. Preencha o `scripts/FEEDBACK.md` (template estruturado)
2. Anexe o `beta_test_report_<data>.json` gerado pelo script
3. Envie para: **feedback@heillon.com**
4. Para bugs urgentes / críticos: assunto "[CRÍTICO] ..."

---

## 🎁 O que você recebe por participar

- ✅ Acesso vitalício ao tier Pro (R$ 299/mês equivalente) por ter
  testado o beta antes do GA
- ✅ Crédito como **Beta Founding User** na changelog pública
- ✅ Linha direta com o time de produto (Discord/Slack privado)
- ✅ 50% de desconto no tier Team se sua organização adotar

Obrigado por estar entre os primeiros. Bom teste!

— Equipe Heillon Legal
