# Heillon Legal — Roadmap Regulatório (Fases 14–17)

**Elaborado:** Maio de 2026  
**Âmbito:** Conformidade regulatória, certificações e enquadramento legal da plataforma

---

## Enquadramento geral

O Heillon Legal opera como plataforma de **IA jurídica com custódia criptográfica** (HDR).  
Pela natureza do produto — tratamento de dados jurídicos, geração de prova técnica, uso de IA em contexto legal — está sujeito a múltiplos regimes regulatórios.

---

## Mapa de obrigatoriedade

### 🔴 Nível 1 — Cumprimento legal obrigatório (risco de sanção imediata)

| Diploma | Artigos críticos | Sanção máxima |
|:---|:---|:---|
| LGPD — Lei 13.709/2018 | Arts. 46-50 (segurança), 52 (sanções ANPD) | 2% do faturamento BR, até R$ 50M por infração |
| Marco Civil — Lei 12.965/2014 | Arts. 13-15 (guarda de logs) | Suspensão da atividade no Brasil |
| ANPD Res. 15/2024 | Arts. 6-12 (notificação incidente 72h) | Advertência, multa, publicação do incidente |
| MP 2.200-2/2001 (ICP-Brasil) | Art. 10 (validade jurídica assinaturas) | Documentos sem validade jurídica em juízo |
| Lei 11.419/2006 | Arts. 1-11 (processo eletrônico) | Nulidade de atos processuais |

### 🟡 Nível 2 — Conformidade de mercado (acesso ao mercado jurídico)

| Diploma | Impacto |
|:---|:---|
| CNJ Res. 615/2025 | Necessário para contratar com Tribunais e órgãos do Judiciário |
| OAB Rec. 001/2024 | Credibilidade com escritórios de advocacia (principais clientes) |
| PL 2338/2023 (Marco Legal IA) | Antecipação obrigatória — texto aprovado no Senado, em análise na Câmara |

### 🟢 Nível 3 — Certificações enterprise (crescimento e internacionalização)

| Padrão | Impacto |
|:---|:---|
| ISO 27001:2022 | Pré-requisito para licitações públicas e grandes escritórios |
| ISO 27701:2019 | Diferencial LGPD+GDPR para clientes multinacionais |
| SOC 2 Type II | Exigido por escritórios internacionais e fundos de investimento |
| EU AI Act 2024/1689 | Obrigatório para operar na UE a partir de agosto/2026 |

---

## Fase 14 — LGPD Técnica + Marco Civil (Sprint 1 — Prioridade crítica)

> **Objetivo:** Eliminar exposição legal imediata. Sem isto, a plataforma opera em infração.

### F14.1 — RIPD automático (Relatório de Impacto à Proteção de Dados)
- Gerar RIPD em PDF/A conforme LGPD art. 38 para cada tipo de tratamento
- Campos obrigatórios: finalidade, base legal, categorias de dados, ciclo de vida, riscos, salvaguardas
- Endpoint `POST /api/v1/compliance/ripd` gera e persiste o relatório
- UI: formulário assistido com exportação PDF assinado

### F14.2 — DPO (Encarregado de Dados) — canal e gestão
- Campo `DPO_EMAIL` + `DPO_NAME` nas configurações
- Endpoint público `GET /api/v1/privacy/dpo-contact` (sem auth)
- Formulário de solicitação de direitos do titular: acesso, correção, exclusão, portabilidade, revogação
- Rastreamento de solicitações com prazo de 15 dias (LGPD art. 19)

### F14.3 — Retenção e eliminação de logs (Marco Civil)
- Logs de acesso à aplicação: retenção mínima 6 meses, eliminação automática após 12 meses
- Logs de conexão: retenção mínima 1 ano
- Tabela `access_logs` com `expires_at`, job de purga semanal
- Política de retenção documentada e exibida na privacidade da plataforma
- Acesso a logs APENAS por ordem judicial (controle de acesso explícito)

### F14.4 — Sistema de notificação de incidentes (ANPD Res. 15/2024)
- Tabela `security_incidents` com campos: detecção, categorização, impacto, titulares afetados
- Workflow: detecção → avaliação → notificação ANPD (≤72h) → notificação titulares
- Endpoint interno `POST /api/v1/security/incident` para registo
- Geração automática de notificação nos moldes da ANPD
- Retenção mínima de 5 anos (art. 48 LGPD + Res. 15/2024)

### F14.5 — Base legal e consentimento granular
- Mapeamento de base legal por tipo de tratamento (consentimento, contrato, legítimo interesse, obrigação legal)
- Consentimento granular na UI: toggle por finalidade com timestamp e versão
- Revogação de consentimento com efeito imediato
- Portabilidade: endpoint `GET /api/v1/privacy/export` devolve ZIP com todos os dados do titular

---

## Fase 15 — ICP-Brasil Qualificada + PDF/A-3 Legal (Sprint 2)

> **Objetivo:** HDRs com validade jurídica plena em processo judicial brasileiro.

### F15.1 — Assinatura qualificada ICP-Brasil (certificado A1/A3)
- Integração com HSM cloud ICP-Brasil (BirdID, VaultID, SafeID) via REST + PKCS#11
- Fallback para certificado A1 soft (arquivo PKCS#12 protegido por senha)
- Assinatura CAdES (CMS Advanced Electronic Signatures) conforme DOC-ICP-15
- Verificação de OCSP/CRL da cadeia de certificação em tempo real

### F15.2 — PDF/A-3 com assinatura embedded
- Migrar de PDF/A-1/B para **PDF/A-3** (permite anexos — chains.json embedded)
- Assinatura PAdES (PDF Advanced Electronic Signatures) conforme ETSI EN 319 100
- Assinatura incorporada ao PDF (não arquivo separado) conforme exigência judicial
- Carimbo de tempo RFC 3161 ICP-Brasil embedded no PDF assinado

### F15.3 — Carimbo de tempo com certificado de cliente ICP-Brasil
- Activar autenticação mTLS no cliente TSA da Certisign/Serpro
- Configuração: `TSA_CLIENT_CERT_PATH`, `TSA_CLIENT_KEY_PATH`
- Validação de OID `2.16.76.1.6.1` (política ICP-Brasil) nos tokens recebidos
- Fallback documentado: FreeTSA (sem presunção legal) para dev/CI

### F15.4 — Verificação de cadeia ICP-Brasil em documentos recebidos
- Ao ingerir evidência PDF, verificar se possui assinatura ICP-Brasil válida
- Registrar resultado no HDR: `icp_brasil_verified: true/false`, cadeia de certificação
- Endpoint `GET /api/v1/verify/icp/{hdr_id}` devolve detalhes da assinatura

---

## Fase 16 — CNJ 615/2025 + OAB + Marco Legal IA (Sprint 3)

> **Objetivo:** Conformidade com o ecossistema jurídico-regulatório específico de IA.

### F16.1 — Classificação de risco dos sistemas de IA
- Documento de classificação para cada agente/modelo: `ai_risk_classification.json`
- Níveis: Mínimo / Limitado / Alto / Inaceitável (conforme CNJ 615 + PL 2338)
- UI: painel "Governança IA" com tabela de risco por agente
- Atualização obrigatória em cada mudança de modelo ou função

### F16.2 — Painel de auditabilidade algorítmica (CNJ 615 art. 2 VII)
- Log de cada decisão de IA: modelo, versão, prompt hash, output hash, timestamp
- Endpoint `GET /api/v1/audit/ai-decisions?mission_id=` com paginação
- UI: linha do tempo de decisões auditável por missão, com exportação CSV
- Retenção: 10 anos (valor probatório judicial)

### F16.3 — Supervisão humana obrigatória para alto risco
- Configurar `REQUIRE_HUMAN_APPROVAL_FOR_HIGH_RISK=true` por tipo de missão
- Gate explícito na UI antes de executar missão classificada como alto risco
- Registro de quem aprovou, quando, e qual o contexto — parte do HDR
- Impossibilidade técnica de bypassar para missões marcadas como alto risco

### F16.4 — Disclosure de IA para clientes (OAB Rec. 001/2024)
- Campo obrigatório no relatório forense: "Este documento foi assistido por IA — modelo: X, versão: Y"
- Funcionalidade de exportação de "Declaração de uso de IA" por missão (PDF assinado)
- Configuração por organização: `REQUIRE_AI_DISCLOSURE=true`
- Histórico de disclosure por cliente/processo

### F16.5 — Documentação de governança IA (PL 2338/2023 readiness)
- Análise de impacto de algoritmos (AIA) para cada tipo de missão de alto risco
- Política de não-discriminação: testes de viés em outputs por categoria
- Registo de incidentes de IA separado do registo geral de incidentes
- Página pública `/governance` com informações sobre a IA usada na plataforma

---

## Fase 17 — ISO 27001 + SOC 2 + EU AI Act Readiness (Sprint 4)

> **Objetivo:** Certificações enterprise e acesso ao mercado internacional.

### F17.1 — ISO 27001:2022 foundation (ISMS)
- Inventário de ativos de informação (hardware, software, dados, serviços)
- Política de segurança da informação documentada e aprovada
- Gestão de riscos: matriz de risco, controles mapeados aos 93 controles ISO
- Plano de tratamento de riscos com responsáveis e prazos

### F17.2 — Controles técnicos ISO 27001 (gaps vs. implementação atual)
- A.8.8 Gestão de vulnerabilidades técnicas → pipeline de dependency scanning (Dependabot)
- A.8.12 Prevenção de perda de dados → DLP básico nos uploads
- A.8.15 Logging (retenção, proteção, acesso) → já parcialmente implementado
- A.8.24 Uso de criptografia → política formal documentando SHA-256, Ed25519, AES-256
- A.8.28 Codificação segura → SAST no CI (Bandit para Python, ESLint security para TS)

### F17.3 — ISO 27701:2019 (PIMS — extensão de privacidade)
- Extensão do ISMS com controles de privacidade (LGPD + GDPR mapeados)
- Registros de atividades de tratamento (RAT) automatizados
- Avaliação de privacidade por design em cada nova feature
- Inventário de transferências internacionais de dados

### F17.4 — SOC 2 Type II readiness
- Trust Services Criteria (TSC) mapeados: Security, Availability, Confidentiality, Privacy
- Implementação dos CC (Common Criteria): CC6 (acesso lógico), CC7 (operações), CC9 (gestão de riscos)
- Monitoramento contínuo de controles via ferramentas automatizadas
- Preparação para período de observação de 6 meses

### F17.5 — EU AI Act (Regulamento 2024/1689) — prazo agosto/2026
- Classificação formal: IA jurídica = **Alto Risco** (Anexo III, ponto 5 — acesso a serviços e benefícios)
- Conformity Assessment (auto-avaliação ou terceiro)
- Technical Documentation conforme Annex IV
- Registo no EU AI Act Database (obrigatório para Alto Risco)
- CE Marking equivalente para produtos de IA
- Incident reporting a autoridades de mercado (≤15 dias)

---

## Cronograma resumido

```
2026  Q2    Q3    Q4
      │     │     │
F14   ████  │     │   ← CRÍTICO — LGPD técnica + Marco Civil
F15   │████ │     │   ← ICP-Brasil qualificada + PDF/A-3
F16   │ ████│     │   ← CNJ 615 + OAB + PL 2338
F17   │     │█████│   ← ISO 27001 foundation + EU AI Act

2027  Q1    Q2
      │     │
F17+  ████  │         ← ISO 27701 + SOC 2 Type II observação
Cert  │ ████│         ← Certificações ISO 27001 + SOC 2 emissão
```

---

## Matriz de risco regulatório atual

| Risco | Probabilidade | Impacto | Fase que mitiga |
|:---|:---|:---|:---|
| Multa ANPD por incidente sem notificação | Alta | Crítico (R$ 50M) | F14.4 |
| Nulidade de HDRs em processo judicial | Alta | Crítico | F15.1-15.2 |
| Exclusão de licitações públicas | Média | Alto | F17.1 |
| Vedação de uso pelo Judiciário (CNJ 615) | Média | Alto | F16.1-16.2 |
| Multa EU AI Act (€35M ou 7% faturamento) | Baixa | Crítico | F17.5 |
| Responsabilidade OAB por uso não supervisionado | Média | Alto | F16.3-16.4 |

---

## Referências normativas

- [LGPD — Lei 13.709/2018](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- [Marco Civil da Internet — Lei 12.965/2014](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm)
- [MP 2.200-2/2001 — ICP-Brasil](https://www.planalto.gov.br/ccivil_03/mpv/antigas_2001/2200-2.htm)
- [Lei 11.419/2006 — Processo Eletrônico](https://www.jusbrasil.com.br/legislacao/95093/lei-de-informatizacao-do-processo-judicial-lei-11419-06)
- [ANPD Res. 15/2024 — Incidentes de Segurança](https://www.lgpd.ms.gov.br/wp-content/uploads/2024/05/REGULAMENTO-DE-COMUNICACAO-DE-INCIDENTE-DE-SEGURANCA-ABRIL-2024-ANPD-.pdf)
- [CNJ Res. 615/2025 — IA no Judiciário](https://atos.cnj.jus.br/atos/detalhar/6001)
- [OAB Rec. 001/2024 — IA na advocacia](https://diario.oab.org.br/pages/materia/842347)
- [PL 2338/2023 — Marco Legal da IA](https://www25.senado.leg.br/web/atividade/materias/-/materia/157233)
- [EU AI Act — Regulamento 2024/1689](https://artificialintelligenceact.eu/high-level-summary/)
- [ISO 27001:2022](https://www.iso.org/standard/27001)
- [ISO 27701:2019 — PIMS](https://www.iso.org/standard/71670.html)
- [ABNT NBR ISO 19005 — PDF/A](https://www.normas.com.br/visualizar/abnt-nbr-nm/27932/abnt-nbriso19005-1)
