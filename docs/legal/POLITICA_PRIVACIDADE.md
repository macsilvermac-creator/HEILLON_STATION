# Política de Privacidade — Heillon Legal

> **STATUS:** TEMPLATE DE BETA PRIVADO. Os campos entre `[[ ... ]]` são
> preenchidos após a liberação do CNPJ. Esta política rege o tratamento de
> dados pessoais na plataforma Heillon Legal ("Heillon", "nós").
>
> **Versão:** 0.1.0-beta · **Vigência a partir de:** `[[DATA_VIGENCIA]]`
> **Última atualização:** `[[DATA_ATUALIZACAO]]`

---

## 1. Quem somos (Controlador)

A Heillon Legal é operada por `[[RAZAO_SOCIAL]]`, inscrita no CNPJ sob o nº
`[[CNPJ]]`, com sede em `[[ENDERECO]]`.

Para fins da Lei nº 13.709/2018 (Lei Geral de Proteção de Dados — **LGPD**),
atuamos como **Controlador** dos dados de cadastro dos usuários da plataforma e
como **Operador** em relação aos dados que você submete para processamento de
IA por meio dos nossos coletores (extensão, gateway de API e console).

**Encarregado de Dados (DPO):** `[[NOME_DPO]]` — `[[EMAIL_DPO]]`
(o contato do DPO também está disponível, sem autenticação, em
`GET /api/v1/privacy/dpo-contact`).

---

## 2. O que o Heillon faz com dados

O Heillon é um **substrato de cadeia de custódia de IA jurídica**. Ele captura
o uso de modelos de IA (prompts, respostas e metadados) e gera **HDRs (Heillon
Detailed Records)** — registros criptográficos imutáveis com:

- hash SHA-256 encadeado ao registro anterior;
- carimbo de tempo (timestamp) — em produção, via Autoridade de Carimbo de
  Tempo credenciada ICP-Brasil;
- assinatura digital Ed25519.

O HDR existe para que o uso de IA tenha **valor probatório auditável**. Ele é,
por natureza e finalidade, **imutável** (ver seção 6).

---

## 3. Dados que tratamos

| Categoria | Exemplos | Base legal (LGPD art. 7º) |
|---|---|---|
| **Cadastro** | nome, e-mail, organização, papel (advogado/perito/admin) | Execução de contrato (V) |
| **Autenticação** | hash da senha (nunca a senha em texto), tokens de sessão | Execução de contrato (V) |
| **Conteúdo de IA** | prompts, respostas, metadados de modelo capturados nos HDRs | Cumprimento de obrigação legal/regulatória (II) e legítimo interesse (IX) na constituição de prova |
| **Logs de acesso** | IP, user-agent, timestamps de requisição | Cumprimento de obrigação legal (II) — Marco Civil, arts. 13–15 |
| **Chaves de API** | apenas o hash SHA-256 (nunca a chave em texto) | Execução de contrato (V) |

**Não tratamos** dados financeiros sensíveis (números de cartão, conta
bancária) na plataforma. Pagamentos, quando houver, são processados fora do
sistema, no site comercial externo.

---

## 4. Compartilhamento

Compartilhamos dados apenas com:

- **Provedores de IA upstream** (OpenAI, Anthropic, Google) — somente quando
  você usa o gateway/extensão e direciona a chamada a esses provedores. O
  Heillon repassa o conteúdo necessário à execução que você solicitou.
- **Autoridade de Carimbo de Tempo (ACT)** ICP-Brasil — recebe apenas o
  *hash* do HDR, nunca o conteúdo.
- **Operadores de infraestrutura** (hospedagem, banco de dados, backup) sob
  contrato com obrigações de confidencialidade.

Nunca vendemos dados pessoais. Nunca compartilhamos conteúdo de HDRs com
terceiros sem ordem judicial ou solicitação expressa do titular/cliente.

---

## 5. Seus direitos (LGPD art. 18)

Você pode, a qualquer momento:

| Direito | Como exercer |
|---|---|
| Confirmação e acesso | `GET /api/v1/privacy/export` (exporta ZIP com seus dados) |
| Correção | atualize seu perfil ou contate o DPO |
| Portabilidade | `GET /api/v1/privacy/export` |
| Revogação de consentimento | `DELETE /api/v1/privacy/consent` |
| **Eliminação da conta** | `DELETE /api/v1/privacy/account?confirm=CONFIRMO_ELIMINACAO` |
| Reclamação à ANPD | [gov.br/anpd](https://www.gov.br/anpd) |

Solicitações também podem ser feitas pelo DPO ou via
`POST /api/v1/privacy/dpo-request`. Respondemos em até **15 dias**.

---

## 6. Retenção e o que permanece após a eliminação

Ao eliminar sua conta, executamos:

1. revogação de todos os consentimentos;
2. **anonimização** do seu cadastro (e-mail, nome e senha são substituídos por
   sentinelas; a conta é desativada);
3. revogação de todas as suas chaves de API;
4. remoção de solicitações pendentes.

**O que NÃO é apagado, e por quê:**

- **HDRs (cadeia de custódia probatória)** — mantidos com base no art. 7º, II
  e art. 16, I e III da LGPD (cumprimento de obrigação legal/regulatória e uso
  exclusivo do controlador, vedado o acesso por terceiros). A cadeia é imutável
  por desígnio: apagar um elo quebraria a prova de todos os elos seguintes.
- **Logs de acesso** — retidos pelo mínimo legal do Marco Civil (6 meses).
- **Registros de incidentes** em que você figure como vítima.

**Retenção por plano (tier):** HDRs de contas do plano *free* são purgados
automaticamente após **30 dias**; *pro* após 365 dias; *team* após 5 anos;
*enterprise* sem expiração. A purga é executada por rotina diária
(`scripts/cron_purge_retention.py`).

---

## 7. Segurança

- Senhas: hash (nunca texto plano).
- Conteúdo sensível em repouso: criptografia Fernet (AES-128) com rotação de
  chaves (MultiFernet).
- Transporte: TLS obrigatório (HSTS).
- Defesa contra SSRF nos gateways; isolamento por organização (multi-tenant).

---

## 8. Cookies

Usamos cookies estritamente necessários (sessão autenticada via cookie
HttpOnly). Não usamos cookies de marketing ou rastreamento de terceiros dentro
da plataforma. O banner de consentimento permite recusar cookies não-essenciais.

---

## 9. Alterações

Mudanças materiais serão comunicadas por e-mail e/ou aviso na plataforma com
antecedência razoável. A versão vigente fica sempre disponível nesta página.

---

## 10. Contato

Dúvidas sobre privacidade: `[[EMAIL_DPO]]`.
Autoridade de controle: ANPD — [gov.br/anpd](https://www.gov.br/anpd).
