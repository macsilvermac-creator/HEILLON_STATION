# Heillon Legal — Referência da API (v1)

Todas as rotas `/api/v1/...` partilham o prefixo definido por `API_V1_PREFIX` (valor por defeito: `/api/v1`). Este documento descreve o **comportamento real** dos modelos FastAPI/Pydantic do repositório (Maio 2026).

**Base típica (dev):** `http://127.0.0.1:8000`  
Exploração interactiva: `GET http://127.0.0.1:8000/docs`

---

## `GET /health`

**200 OK**

```json
{ "status": "ok" }
```

*Não existe campo `version` neste MVP.*

---

## Evidence — `POST /api/v1/ingestion`

`multipart/form-data`

| Campo | Obrigatoriedade |
|:---|:---|
| `file` | Sim |
| `mission_id` | Não — se omitido sintetiza-se `mission_{uuid}` |
| `previous_hdr` | Não — encadeia HDR de ingestão |

**200 OK** (`IngestionResponse`)

```json
{
  "hdr": {
    "hdr_id": "<64 hex minúsculo>",
    "hdr_version": "1.0",
    "hdr_type": "ingestion",
    "mission_id": "...",
    "timestamp": "<ISO8601 Z>",
    "timestamp_trusted": "<base64 PKCS#11 ou stub>",
    "agent": { "id": "...", "model": "...", "version": "..." },
    "user": { "id": "anonymous_uploader", "signature": null },
    "intent": { "...": "..." },
    "execution": {
      "status": "completed",
      "input_hash": "<SHA-256 hex 64 chars>",
      "output_hash": "<SHA-256 hex 64 chars | null>",
      "duration_ms": 0
    },
    "cognitive_snapshot": { "...": "..." },
    "normative": { "checked": true, "violations": [], "corpus_version": "..." },
    "previous_hdr": null,
    "supersedes": null,
    "corrects": null,
    "canonical_hash": "<igual ao hdr_id quando íntegro>"
  },
  "evidence_storage_path": "<caminho absoluto no servidor>"
}
```

---

## HDR — Verificação pública

### `GET /api/v1/verify/{hdr_id}`

**200 OK** (`VerificationResponse`)

Campos relevantes:

- `valid`: booleano
- `integrity_status`: `"validated"` ou `"compromised"`
- `timestamp_status`: `"trusted"` ou `"invalid"`
- `chain_status`: `"singular"` (verificação de item isolado)
- `details.steps`: texto explicativo curto para auditores

### `GET /api/v1/verify/chain/{mission_id}`

Exige pelo menos um HDR gravado para a missão; caso contrário **404**.

**200 OK** (`ChainVerificationResponse`)

- `integrity_status`: `"validated"` / `"compromised"`
- `timestamp_status`: espelho coerente com `integrity_status`
- `chain_status`: `"linear"` quando a cadeia é válida, `"fractured"` quando quebrada
- `verification`: objecto `ChainVerificationDetails` (`steps`)

---

## Mission — Ciclo EASY

Todos os payloads de missão usam `MissionPlan`, `DAG`, `DAGNode` e enums em minúsculas (`MissionStatus.pending`, etc.) conforme FastAPI/OpenAPI.

### `POST /api/v1/mission/plan`

**Body JSON**

```json
{
  "description": "Texto livre PT/EN misturado aceite",
  "authorized_agents": ["ocr-agent", "analysis-agent"]
}
```

Campo **`authorized_agents`** (nome API) é mapeado internamente para `authorized_agent_ids` no modelo `MissionPlan`.

**200 OK**: `MissionPlan` completo, inclui `dag`, `normative_result`, `status` inicial `pending`, `estimated_cost_gas`.

### `POST /api/v1/mission/{mission_id}/approve`

Fluxos típicos:

- **403**: missão barrada pelo corpus (`normative_result.allowed == false`)
- **409**: já não está `pending`

**200 OK**: mesmo esquema `MissionPlan`, `status` → `approved`.

### `POST /api/v1/mission/{mission_id}/execute`

Requisitos: `approved` **e** normativa permissiva.

- **409**/`400` conforme conflitos de ciclo ou DAG inválido
- **200 OK** (`MissionExecutionResult`): inclui **`hdrs` completos**, `total_hdrs`, `chain_root` / `chain_tail`.

### `GET /api/v1/mission/` (lista)

Query: `skip`, `limit`.

### `GET /api/v1/mission/{mission_id}`

Hydratação direta da linha SQLite — **404** quando inexistente.

### `GET /api/v1/mission/diary`

Query opcional:

| Parâmetro | Descrição |
|:---|:---|
| `skip`, `limit` | Paginação (`limit`≤200) |
| `status` | enum `MissionStatus` serializado como string (`completed`, ...) |
| `date_from`, `date_to` | ISO date friendly para `datetime(SQLite comparisons)` |
| `search` | `LIKE` sobre `missions.description` |

**200 OK** (`MissionDiaryResponse`)

```json
{
  "total": 12,
  "skip": 0,
  "limit": 20,
  "missions": [ { "...MissionPlan..." } ]
}
```

### `GET /api/v1/mission/diary/stats`

**200 OK** (`MissionStats`)

```json
{
  "total_missions": 12,
  "completed": 4,
  "failed": 0,
  "blocked_by_normative": 2,
  "total_hdrs_generated": 9,
  "avg_execution_time_ms": 842.17,
  "most_used_agents": [
    { "agent_id": "analysis-agent", "count": 5 }
  ]
}
```

`most_used_agents` conta nós DAG persistidos histórico, não apenas execuções concluídas.

---

## Normative — `GET /api/v1/normative/rules`

**200 OK**: lista de `NormativeRule` ordenada por prioridade descendente conforme implementação (`get_active_rules`).

---

## Forensic — Pacotes judiciais (MVP técnico)

### `POST /api/v1/forensic/package/{mission_id}?generated_by=<str>`

Só faz sentido quando a linha SQLite da missão está `completed` e existem HDRs filho.

**Erros**:

- **400** com `detail` textual se missão incompleta / ausência de cadeia

**200 OK** (`ForensicPackage`):

```json
{
  "package_id": "fpkg_<hash derivado deterministicamente>",
  "mission_id": "...",
  "status": "completed",
  "manifest": {
    "package_id": "fpkg_...",
    "mission_id": "...",
    "chain_root": "...",
    "chain_tail": "...",
    "total_hdrs": 3,
    "generated_at": "<datetime ISOAware>",
    "generated_by": "perito...",
    "integrity_hash": "<SHA-256 hex>",
    "verification_url": "<base VERIFICATION_PUBLIC_BASE>/api/v1/verify/<chain_tail>"
  },
  "pdf_checksum": "...",
  "json_chain_checksum": "...",
  "created_at": "<datetime>",
  "download_url": "/api/v1/forensic/package/fpkg_…/download/manifest"
}
```

O download “PDF” continua sendo, nesta fase, um **ficheiro texto** (`media_type=text/plain`; nome sugere relatório executivo até integração PDF/A).

### Downloads

| Método | Caminho |
|:---|:---|
| `GET` | `/api/v1/forensic/package/{package_id}/download/pdf` |
| `GET` | `/api/v1/forensic/package/{package_id}/download/json` |
| `GET` | `/api/v1/forensic/package/{package_id}/download/manifest` |

**404** se o pacote não existir.

---

## Observações globais para integradores jurídicos

1. **Sem autenticação** nos endpoints públicos `/verify/**` ou ingestão atual — aplique gateways reversos antes de exposição WAN.
2. **Verificação** depende exclusivamente das assinaturas internas HDR + RFC3161; qualquer modificação SQLite quebra `verify`.
3. **Forensic** repetido para a mesma missão faz `INSERT OR REPLACE` — revise política retention no vosso *file store* antes de arquivo WORM físico.

Para histórico de QA: `pytest` na raíz `backend/` e `tests/domain/**`; integração feliz documentada por `tests/integration/test_full_mission_flow.py`.
