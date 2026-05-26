# HEILLON-LEGAL — Contexto Técnico (Fase 20 — Sistema Definitivo Global)

**Documento vivo** para onboarding de engenharia e alinhamento com o briefing jurídico Heillon (**Legitimidade Computacional**, Mai 2026).  
O código em `backend/app/domain/` é a fonte de verdade; este ficheiro descreve comportamento, decisões e arquitetura atual.

**Estado:** Produção — Fase 20 completa  
**Testes:** 272 (pytest -q, todos verdes)  
**Rotas frontend:** 32 (npm run build, zero erros TypeScript)

---

## Ecossistema

- [https://heillon.com](https://heillon.com) — site institucional
- [https://hdr.heillon.com](https://hdr.heillon.com) — portal público de verificação HDR
- [https://heillon-legal-ui.vercel.app](https://heillon-legal-ui.vercel.app) — UI em produção (Vercel)

---

## Arquitetura DDD — Bounded Contexts (18 domínios)

Cada domínio em `backend/app/domain/` contém:
- **`models.py`** — entidades e VOs Pydantic v2
- **`services.py`** — regra de negócio
- **`repository.py`** — abstração de persistência (PostgreSQL prod / SQLite dev)
- **`api.py`** — router FastAPI

| Domínio | Pasta | Responsabilidade |
|:---|:---|:---|
| **HDR** | `hdr/` | Geração HDR (SHA-256 + RFC 3161), ICP-Brasil TSA, verificação criptográfica, rotas `/verify/*` |
| **Evidence** | `evidence/` | Ingestão multipart, hashing, PyMuPDF/python-docx, WORM storage |
| **Mission** | `mission/` | OrchestrationEngine EASY, lexicon, aprovação humana, DAG, executores LLM/Stub |
| **Normative** | `normative/` | Corpus normativo FTS5, política pré-execução, 5+ frameworks |
| **Forensic** | `forensic/` | Pacotes forenses, relatório executivo, chain.json, manifesto de integridade |
| **User** | `user/` | Autenticação JWT (cookie HttpOnly), registo, RBAC, organização multi-tenant |
| **Mobile** | `mobile/` | Push tokens, estatísticas PWA, rotas `/m/*` |
| **Privacy** | `privacy/` | LGPD técnica: RIPD PDF, DPO SLA 15d, portabilidade ZIP, incidentes ANPD 72h |
| **Signatures** | `signatures/` | Assinaturas digitais universais: ICP-Brasil CAdES-BES, eIDAS QES/PAdES-LTA, ESIGN, UAE-PASS |
| **Governance** | `governance/` | CNJ 615/2025, OAB Rec. 001/2024, AI decision audit log, human approval gates |
| **EU AI Act** | `euaiact/` | EU AI Act 2024/1689, GDPR, eIDAS 2.0, ISO 27001 ISMS, Annex IV tech docs, DPIA |
| **USA** | `usa/` | Colorado AI Act SB 205, CCPA/CPRA, ABA Model Rules, NIST AI RMF 1.0, ESIGN |
| **UAE** | `uae/` | UAE PDPL Decreto 45/2021, DIFC, ADGM, UAE AI Ethics, UAE PASS |
| **APAC** | `apac/` | UK GDPR, Singapore PDPA + Agentic AI, Australia Privacy Act, Canada PIPEDA/C-27 |
| **ISO 42001** | `iso42001/` | AIMS completo, FRIA (EU AI Act Art. 27), controles Annex A |
| **Legal Evidence** | `legal_evidence/` | FRE 707, citações com fonte, detecção de alucinações, competência OAB/ABA |
| **Malpractice** | `malpractice/` | Malpractice Insurance Score, Colorado SB 26-189, CCPA ADMT |
| **HDR ICP** | `hdr/icp_brasil.py` | TSA fallback chain: Certisign → Serpro → FreeTSA → stub (só dev/CI) |

---

## Ciclo Jurídico Fim-a-Fim

```
1. EVIDENCE
   Upload multipart → extração de texto (PyMuPDF/python-docx) → SHA-256 → HDR ingestion
   → disco WORM (EVIDENCE_DIR) → resposta com hdr_id

2. MISSION PLAN
   Linguagem natural + authorized_agents
   → lexicon.KEYWORD_AGENT_MAP → DAG linear
   → NormativeService.check_intent (FTS5 corpus)
   → CNJ/OAB governance check

3. BLOQUEIO NORMATIVO
   normative_result.allowed == false → HTTP 403 em /approve
   Missão permanece PENDING sem execução

4. APROVAÇÃO HUMANA
   POST /mission/{id}/approve (operador autenticado no tenant)
   → governance: human approval gate logged

5. EXECUÇÃO EASY
   OrchestrationEngine.execute_mission (estado APPROVED)
   → cada nó: AgentConfigService.resolve_executor()
     - Tenant configurado: OpenAI/Anthropic/Ollama real
     - Fallback estático: DeterministicStubMissionExecutor
   → gera HDR encadeado (previous_hdr), TSA ICP-Brasil

6. PACOTE FORENSE
   forensic/services.py → relatório executivo + chain.json + manifesto
   → ICP-Brasil: icp_signer.py (A1 PKCS#12 / CAdES-BES) quando configurado
   → PDF/A-3 com AF chains.json quando pdfa3_service disponível

7. VERIFICAÇÃO PÚBLICA
   GET /verify/{hdr_id} ou /verify/icp/{hdr_id} — sem autenticação
   Qualquer tribunal/terceiro valida hash, encadeamento, carimbo TSA
```

---

## Infraestrutura Partilhada

```
app/core/
  config.py          — Settings Pydantic v2, validações prod (FERNET obrigatório, stub proibido)
  security_headers.py — SecurityHeadersMiddleware (CSP, HSTS, XFO, Referrer-Policy)
  logging_config.py  — JSON estruturado em produção, colorido em dev
  security.py        — JWT + cookie HttpOnly, bcrypt, Fernet para chaves de agentes

app/db/
  database.py        — SQLAlchemy async (PostgreSQL prod / SQLite dev)
  migrations/        — 009+ ficheiros SQL (normative_fts, privacy, signatures, …)

app/dependencies.py  — get_db, get_current_user (cookie HttpOnly)
```

---

## Frontend Next.js 15 (App Router)

| Rota | Área |
|:---|:---|
| `/` | Landing + Hero 3D (Three.js, frameloop="demand") |
| `/dashboard` | Painel geral com gráficos (Recharts lazy) |
| `/ingestion` | Upload de evidências |
| `/missions`, `/missions/[id]` | EASY missions cockpit |
| `/verification` | Portal verificação pública |
| `/compliance` | Relatório conformidade LGPD/GDPR + download PDF |
| `/normative` | Corpus normativo + FTS5 |
| `/privacy` | Centro de privacidade LGPD (consentimento, portabilidade, RIPD) |
| `/agent-config` | Soberania de modelos (Ollama, OpenAI, Anthropic, custom) |
| `/docs/*` | Central de documentação (10+ páginas) |
| `/health` | Health dashboard (admin) |
| `/m/*` | Shell móvel PWA |

**Componentes críticos:**
- `FolderTopbar` — navegação gold filing-drawer (67 px, TOPBAR_H constante)
- `ConditionalAppShell` — aplica `paddingTop: TOPBAR_H` ao conteúdo
- `AuthProvider` — HttpOnly cookie via `fetchCurrentUser()`, localStorage apenas para cache não sensível
- Proxy Route Handler (`/api/v1/[...path]`) — repassa cookies HttpOnly ao backend sem CORS

---

## Segurança de Runtime

| Camada | Mecanismo |
|:---|:---|
| Autenticação | JWT em cookie HttpOnly (`heillon_session`), sem bearer em localStorage |
| Autorização | RBAC por role (advogado / admin), `organization_id` multi-tenant |
| Chaves de agentes | Fernet (obrigatório em produção, distinto do JWT secret) |
| Headers HTTP | CSP, HSTS, X-Frame-Options, Referrer-Policy, Permissions-Policy |
| Rate limiting | Redis 7 distribuído + fallback em memória |
| Timestamps | TSA ICP-Brasil real (FORCE_STUB_TIMESTAMP=false em produção) |
| Next.js | ≥ 15.4.10 (patches CVE-2025-55183, CVE-2025-55184, CVE-2025-67779) |

---

## Variáveis de Ambiente Obrigatórias em Produção

| Variável | Obrigatória | Notas |
|:---|:---|:---|
| `AUTH_SECRET_KEY` | ✅ | ≥32 chars, não pode ser o default `dev-insecure-*` |
| `FERNET_ENCRYPTION_KEY` | ✅ | Base64 URL-safe, distinto do JWT secret |
| `POSTGRES_PASSWORD` | ✅ | Não pode ser `changeme` |
| `ENVIRONMENT` | ✅ | `production` — ativa todas as validações de segurança |
| `VERIFICATION_PUBLIC_BASE` | ✅ | URL pública da instância (ex.: https://heillon-legal-ui.vercel.app) |
| `FORCE_STUB_TIMESTAMP` | ❌ | `false` (default); nunca `true` em produção |
| `TSA_PROVIDER` | — | `certisign` \| `serpro` \| `freetsa` \| `stub` (só dev/CI) |

---

## Cobertura Regulatória (Fase 20)

| Jurisdição | Diploma(s) | Fase |
|:---|:---|:---|
| 🇧🇷 Brasil | LGPD, Marco Civil, ANPD, ICP-Brasil, CNJ 615/2025, OAB | 14–16 |
| 🇪🇺 União Europeia | EU AI Act, GDPR, eIDAS 2.0, ISO 27001 ISMS | 17 |
| 🇺🇸 EUA | Colorado SB 205, CCPA/CPRA, ABA Rules, NIST AI RMF | 18 |
| 🇦🇪 EAU | UAE PDPL, DIFC, UAE AI Ethics, UAE PASS | 19 |
| 🌏 APAC | UK GDPR, Singapore PDPA, Australia Privacy Act, Canada PIPEDA/C-27 | 20 |
| 🏅 Global | ISO 42001:2023 AIMS, FRIA, Legal Evidence (FRE 707), Malpractice Score | 20 |

---

## Roadmap Próximo — Fase 21

| Item | Descrição |
|:---|:---|
| ISO 27001 completo | Auditoria externa + certificação (ISMS) |
| ISO 27701 (PIMS) | Privacy Information Management System |
| SOC 2 Type II | Trust Services Criteria para enterprise EUA |
| Relatório forense PDF/A-3 assinado | Substituir relatório executivo estruturado por PDF/A-3 + CAdES-BES completo |
| Executores LLM por tenant | Onboarding automatizado de OpenAI/Anthropic/Ollama por organização |

---

*Última atualização: 25 de maio de 2026 — Fase 20 completa.*
