# RIPD/DPIA — Relatório de Impacto à Proteção de Dados do Heillon Legal

> Relatório de Impacto à Proteção de Dados Pessoais (LGPD art. 38) do **próprio
> sistema Heillon Legal**, enquanto produto que trata dados pessoais.
>
> **Versão:** 0.1.0-beta · **Elaborado por:** `[[NOME_DPO]]` (DPO) ·
> **Data:** `[[DATA]]` · **Status:** rascunho de beta (revisar após CNPJ)

---

## 1. Identificação do tratamento

| Item | Descrição |
|---|---|
| **Sistema** | Heillon Legal — substrato de cadeia de custódia de IA jurídica |
| **Controlador** | `[[RAZAO_SOCIAL]]` (CNPJ `[[CNPJ]]`) |
| **Finalidade** | Gerar registros criptográficos imutáveis (HDRs) do uso de IA, com valor probatório auditável |
| **Natureza** | Coleta, registro, armazenamento, encadeamento criptográfico, carimbo de tempo, eliminação por retenção |
| **Escopo** | Beta privado (~50 advogados convidados) |

---

## 2. Necessidade e proporcionalidade

- **Minimização:** o sistema captura apenas o necessário para constituir prova
  (prompt, resposta, metadados de modelo). Não há coleta de dados de cartão,
  conta bancária ou biometria.
- **Base legal:** execução de contrato (cadastro); cumprimento de obrigação
  legal/regulatória e legítimo interesse na constituição de prova (HDRs);
  obrigação legal (logs Marco Civil).
- **Proporcionalidade:** a imutabilidade dos HDRs é proporcional à finalidade
  probatória — registros mutáveis não teriam valor de cadeia de custódia.

---

## 3. Categorias de dados e titulares

| Titular | Dados | Sensível? |
|---|---|---|
| Usuário (advogado/perito) | nome, e-mail, organização, papel | Não |
| Usuário | hash de senha, tokens, hash de API key | Não (credenciais protegidas) |
| Terceiros citados no conteúdo | o que o usuário inserir nos prompts | **Possivelmente** (depende do uso) |

> ⚠️ **Risco de dado sensível embutido em conteúdo:** o usuário pode inserir
> dados de saúde, processos, etc. nos prompts. Mitigação: orientação no manual
> + responsabilidade do usuário (Termos seção 5) + isolamento multi-tenant +
> criptografia em repouso.

---

## 4. Riscos identificados e medidas

| # | Risco | Probab. | Impacto | Medida mitigadora |
|---|---|---|---|---|
| R1 | Vazamento de conteúdo de HDR | Baixa | Alto | Criptografia Fernet (MultiFernet/rotação), TLS/HSTS, isolamento por org, RLS no PostgreSQL |
| R2 | Acesso indevido entre organizações | Baixa | Alto | Multi-tenant com filtro obrigatório por `organization_id`; Row-Level Security |
| R3 | Vazamento de credenciais | Baixa | Alto | Senha e API key apenas como hash SHA-256; cookie HttpOnly+Secure; JWT sem default em produção |
| R4 | SSRF via gateway (URL upstream) | Média | Médio | Resolução DNS + bloqueio de IPs privados/loopback antes da chamada |
| R5 | Retenção excessiva | Baixa | Médio | Purga automática por tier (30d free); purga de logs Marco Civil |
| R6 | Carimbo de tempo sem valor jurídico | Média | Alto | Em produção, ACT credenciada ICP-Brasil (Serpro/Certisign); `FORCE_STUB_TIMESTAMP` proibido em produção |
| R7 | Perda de dados (indisponibilidade) | Baixa | Médio | Backup diário criptografado (pg_dump), runbooks de restauração |
| R8 | Dado sensível embutido em prompt | Média | Médio | Orientação + Termos; criptografia; minimização |

---

## 5. Direitos dos titulares

Implementados via endpoints `/api/v1/privacy/*`:
acesso/portabilidade (`/export`), revogação de consentimento (`/consent`),
**eliminação** (`/account`), canal do DPO (`/dpo-request`, `/dpo-contact`).
Prazo de resposta: 15 dias.

---

## 6. Transferência internacional

Provedores de IA upstream (OpenAI, Anthropic, Google) podem processar dados
fora do Brasil. Tratado como transferência internacional (LGPD art. 33). O uso
desses provedores é **opcional e direcionado pelo usuário**; o conteúdo enviado
é o necessário à execução solicitada.

---

## 7. Incidentes

Processo de registro e notificação à ANPD implementado
(`/api/v1/security/incident` + gerador de rascunho de notificação,
ANPD Res. 15/2024). Runbook: `RUNBOOK_INCIDENTE.md`.

---

## 8. Conclusão do DPO

`[[PARECER_DPO]]` — Risco residual avaliado como **`[[BAIXO/MÉDIO]]`** para a
fase de beta privado, condicionado a: (a) contratação de ACT ICP-Brasil antes
do GA; (b) revisão deste RIPD após liberação do CNPJ; (c) execução dos backups
e purgas conforme runbooks.

Assinatura: `[[NOME_DPO]]` — `[[DATA]]`.
