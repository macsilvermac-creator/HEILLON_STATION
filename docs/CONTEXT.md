# HEILLON-LEGAL — Contexto técnico (Fase 3)

Documento vivo para onboarding de engenharia e alinhamento com o briefing jurídico Heillon (**Legitimidade computacional**, Mai 2026). O código em `backend/app/domain/` é a fonte de verdade; este ficheiro descreve comportamento e decisões.

## Ecossistema

- [https://heillon.com](https://heillon.com) · [https://vitrine.heillon.com](https://vitrine.heillon.com) · [https://hdr.heillon.com](https://hdr.heillon.com)

## Arquitectura DDD (bounded contexts)

O backend foi reorganizado por **domínios isolados**. Cada domínio contém habitualmente:

- **`models.py`** — entidades e VOs em Pydantic
- **`services.py`** — regra de negócio (onde aplicável)
- **`repository.py`** — abstração de persistência (SQLite neste MVP)
- **`api.py`** — router FastAPI

| Domínio | Pasta `app/domain/` | Responsabilidade |
|:---|:---|:---|
| **HDR** | `hdr/` | Geração de HDR (`HDRService`), verificação criptográfica, carimbo **RFC3161** (`timestamp_service`), rotas públicas `/verify/*` |
| **Evidence** | `evidence/` | Ingestão multipart, hashing de ficheiros, armazenamento no `EVIDENCE_DIR`, associação a HDR ingestion |
| **Mission** | `mission/` | `OrchestrationEngine` (*keyword→agente* via `lexicon.py`), aprovação humana PENDING→APPROVED, execução DAG (stubs), **Diário de bordo**, listagem `/mission/` |
| **Normative** | `normative/` | `NormativeRepository` em memória + `NormativeService` (regras padrão LEGAL‑001…005), política antes da execução |
| **Forensic** | `forensic/` | Pacotes forenses: relatório textual stub, JSON canonical da linhagem HDR, manifesto de integridade, caminhos em `FORENSICS_PACKAGE_DIR` |

**Infraestrutura partilhada** (`app/core/`, `app/db/`, `app/dependencies.py`) não pertence a um domínio de negócio — configura segurança, JSON canónico e ligações SQLite.

### Acoplamento entre domínios

- **Missão** pode referenciar `NormativeResult` no modelo porque o plano jurídico embute o resultado do corpus na mesma unidade persistente (`mission_plan_snapshot` em SQLite).
- A orquestração invoca **`HDRService`** e **`NormativeService`** por composição na `OrchestrationEngine`, não através de routers.

## Ciclo jurídico fim‑a‑fim (modelo conceptual)

```
1. EVIDENCE — Upload → SHA‑256 determinístico → HDR `ingestion` → disco WORM (`EVIDENCE_DIR`)

2. MISSION PLAN — Linguagem natural + lista de agentes autorizados (`authorized_agents`)
                 → seleção lexical (`lexicon.KEYWORD_AGENT_MAP`)
                 → DAG linear com dependências
                 → Corpus normativo avalia INTENTO (`normative_service.check_intent`)

3. MISSÃO BLOQUEADA — `normative_result.allowed == false`: DAG pode ficar vazio; nunca há execução
                      (fluxo REST devolve HTTP 403 em *approve*, se aplicável ao estado).

4. APROVAÇÃO HUMANA — `POST /mission/{id}/approve` apenas se normativa permissiva.

5. EXECUÇÃO — `OrchestrationEngine.execute_mission` só com estado APPROVED
              → cada nó chama `check_action`
              → gera HDR coerente (`hdr_service.generate_hdr`), encadeamento `previous_hdr`

6. PACOTE FORENSE — apenas se existir linha de missão `completed` no SQLite e HDRs presentes:
                    stub executivo `.txt`, `chain.json`, manifest + `verification_url`
                    (+ hash de pacote determinísticos em função das checksums intermedias)

7. VERIFICAÇÃO PÚBLICA — sem autenticação; qualquer tribunal ou terceiro valida hashes e ligações.
```

## Persistência SQLite

Migrada incrementalmente sob `backend/app/db/migrations/` (`hdrs`, `missions`, `forensic_packages`). O snapshot JSON das missões é a fonte de verdade hidratada pelo Pydantic (atenção a datas ISO e `DAG.edges` com listas vindas do JSON).

## Frontoffice Next.js

- App Router cliente → **API v1** documentada em `docs/API-REFERENCE.md`.
- `NEXT_PUBLIC_BACKEND_URL` aponta para o mesmo *origin* público esperado pela verificação se quiseremos alinhar *marketing* ao backend (default dev: porta 8000).

## Segurança do runtime Next.js

Aplicações com **App Router** dependem das versões patched indicadas pela Vercel (ex.: `next@15.4.10` na série 15.4.x) para CVEs CVE-2025-55183, CVE-2025-55184 e CVE-2025-67779 documentados na actualização [11 Dez 2025](https://nextjs.org/blog/security-update-2025-12-11).

## Estado da arte vs roadmap

✅ Ledger HDR determinístico, ingestão WORM pública verificável, EASY com DAG stubs, Corpus normativo, Diário forense/estatísticas, Frontend integrado ao backend com build verde.

⏭️ Agentes OCR/IAS reais, PDF/A com assinatura qualificada, autenticação de utilizadores, vector store (`sqlite‑vss` ou serviço dedicado), *hardening* da superfície pública `/verify`.
