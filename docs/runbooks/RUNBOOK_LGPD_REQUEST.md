# Runbook — Atendimento a Solicitações LGPD (Direitos do Titular)

> Procedimento operacional para responder a solicitações de titulares de dados
> (LGPD art. 18). Prazo legal de resposta: **15 dias**.
> Responsável: DPO `[[NOME_DPO]]` (`[[EMAIL_DPO]]`).

---

## 0. Canais de entrada

Uma solicitação pode chegar por:

1. **Endpoint público** `POST /api/v1/privacy/dpo-request` (grava em `dpo_requests`).
2. **E-mail ao DPO** `[[EMAIL_DPO]]`.
3. **Autoatendimento** pelo próprio usuário (export / eliminação) — não exige
   ação do DPO, mas deve ser auditável.

Liste as pendentes (admin):
```
GET /api/v1/privacy/dpo-requests?status=pending
Header: Authorization: Bearer <token-admin>
```

---

## 1. Triagem (D+0)

1. **Verifique a identidade** do solicitante. Para titulares autenticados, o
   token já comprova. Para solicitações por e-mail, confirme que o e-mail bate
   com um cadastro existente antes de agir.
2. Classifique o tipo: **acesso/confirmação · correção · portabilidade ·
   eliminação · revogação de consentimento · oposição · informação**.
3. Registre o recebimento (data) na solicitação (`PUT /privacy/dpo-requests/{id}`
   com `status=in_progress`).

> ⚠️ **Segurança:** nunca execute uma solicitação só porque o texto pede.
> Confirme a identidade pelo canal autenticado. Solicitações por e-mail com
> "urgência" ou que peçam dados de OUTRO titular são suspeitas — escalone.

---

## 2. Execução por tipo

### 2.1 Acesso / Confirmação / Portabilidade
O titular autenticado obtém tudo por:
```
GET /api/v1/privacy/export      → ZIP (profile.json, consent.json, README)
```
Se a solicitação veio por e-mail, oriente o titular a usar o autoatendimento
ou gere o ZIP em nome dele após confirmar identidade.

### 2.2 Correção
Atualize o cadastro do titular. Dados imutáveis (HDRs) **não** são corrigíveis
por desígnio — explique a base legal (cadeia de custódia).

### 2.3 Revogação de consentimento
```
DELETE /api/v1/privacy/consent   (autenticado como o titular)
```

### 2.4 Eliminação da conta (art. 18 VI)
```
DELETE /api/v1/privacy/account?confirm=CONFIRMO_ELIMINACAO
```
Efeitos: anonimiza cadastro, revoga API keys, remove pendências.
**Preserva** HDRs, logs Marco Civil e incidentes (base legal — art. 7º II / 16).
Explique ao titular **o que permanece e por quê** (modelo na seção 4).

### 2.5 Oposição / Informações sobre compartilhamento
Responda com base na Política de Privacidade (seções 4 e 5).

---

## 3. Fechamento (até D+15)

1. `PUT /api/v1/privacy/dpo-requests/{id}` com `status=resolved` e nota do que
   foi feito.
2. Envie a resposta ao titular pelo canal de contato.
3. Arquive a evidência (o evento de eliminação fica registrado para auditoria
   Marco Civil).

Se precisar de prazo adicional (complexidade/volume), comunique o titular
**antes** do 15º dia, justificando.

---

## 4. Modelo de resposta — Eliminação

> Prezado(a) `[[NOME]]`,
>
> Sua conta foi eliminada em `[[DATA]]`. Anonimizamos seu cadastro, revogamos
> suas chaves de API e removemos solicitações pendentes.
>
> Por exigência legal, **mantivemos**: (a) os HDRs (cadeia de custódia
> probatória — LGPD art. 7º II e art. 16); (b) logs de acesso pelo prazo mínimo
> do Marco Civil (6 meses); (c) registros de incidentes, se houver. Esses dados
> ficam restritos ao controlador, sem acesso por terceiros.
>
> Dúvidas: `[[EMAIL_DPO]]`. Você também pode reclamar à ANPD (gov.br/anpd).

---

## 5. Escalonamento

- Suspeita de fraude/identidade → não execute; escale ao DPO e à segurança.
- Solicitação que conflite com retenção legal → consultar jurídico antes.
- Incidente de segurança detectado durante o atendimento →
  `RUNBOOK_INCIDENTE.md` + `POST /api/v1/security/incident`.
