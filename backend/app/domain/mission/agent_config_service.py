"""Per-tenant configuration driving which cognition backend each EASY agent invokes."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Generator

from cryptography.fernet import InvalidToken

from app.core.config import Settings, get_settings
from app.db.compat import CompatConnection, open_connection, resolve_dialect
from app.domain.mission.agent_config_crypto import build_config_fernet
from app.domain.mission.agent_config_models import AgentConfig, AgentConfigUpdate, AgentModelSource
from app.domain.mission.agent_execution import MissionAgentExecutor
from app.domain.mission.executors_anthropic import AnthropicMessagesMissionExecutor
from app.domain.mission.executors_llm import OpenAICompatibleMissionExecutor
from app.domain.mission.executors_stub import DeterministicStubMissionExecutor
from app.domain.mission.models import AgentDefinition, DAGNode


DEFAULT_OLLAMA_V1_BASE = "http://127.0.0.1:11434/v1"
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_ANTHROPIC_BASE = "https://api.anthropic.com"


@dataclass(frozen=True)
class _StoredCipher:
    """Internal row prior to sanitized HTTP projection."""

    agent_id: str
    organization_id: str
    source: AgentModelSource
    model_name: str | None
    api_base_url: str | None
    api_key_encrypted: bytes | None
    updated_at: datetime


class AgentConfigService:
    """Persistência de configuração de agentes (SQLite dev / PostgreSQL produção)."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        database_path: Path | None = None,
        secret_material: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._legacy_sqlite_path = database_path.expanduser().resolve() if database_path else None
        self._fernet = build_config_fernet(secret_material=secret_material)

    @contextmanager
    def _connect(self) -> Generator[CompatConnection | sqlite3.Connection, None, None]:
        if self._legacy_sqlite_path is not None and resolve_dialect(self._settings) == "sqlite":
            self._legacy_sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            raw = sqlite3.connect(self._legacy_sqlite_path.as_posix(), check_same_thread=False)
            raw.row_factory = sqlite3.Row
            try:
                yield raw
                raw.commit()
            except Exception:
                raw.rollback()
                raise
            finally:
                raw.close()
            return

        with open_connection(self._settings) as conn:
            yield conn

    @staticmethod
    def _decode_row(row: Any) -> _StoredCipher | None:
        if row is None:
            return None
        cipher_blob = row["api_key_encrypted"]
        token_bytes: bytes | None
        if cipher_blob is None:
            token_bytes = None
        elif isinstance(cipher_blob, memoryview):
            token_bytes = cipher_blob.tobytes()
        else:
            token_bytes = bytes(cipher_blob)

        updated_raw = str(row["updated_at"])
        try:
            parsed = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
        except ValueError:
            parsed = datetime.now(UTC)

        return _StoredCipher(
            agent_id=str(row["agent_id"]),
            organization_id=str(row["organization_id"]),
            source=AgentModelSource(str(row["source"])),
            model_name=row["model_name"],
            api_base_url=row["api_base_url"],
            api_key_encrypted=token_bytes,
            updated_at=parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC),
        )

    def _decrypt_key(self, blob: bytes | None) -> str | None:
        if not blob:
            return None
        try:
            return self._fernet.decrypt(blob).decode("utf-8")
        except InvalidToken:
            return None

    def _encrypt_key(self, plain: str | None) -> bytes | None:
        if plain is None or plain == "":
            return None
        return self._fernet.encrypt(plain.encode("utf-8"))

    def _fetch(self, conn: Any, agent_id: str, organization_id: str) -> _StoredCipher | None:
        row = conn.execute(
            """SELECT agent_id, organization_id, source, model_name, api_base_url,
                      api_key_encrypted, updated_at
               FROM agent_configs
               WHERE agent_id = ? AND organization_id = ?""",
            (agent_id, organization_id),
        ).fetchone()
        return self._decode_row(row)

    def _to_public(self, row: _StoredCipher) -> AgentConfig:
        return AgentConfig(
            agent_id=row.agent_id,
            organization_id=row.organization_id,
            source=row.source,
            model_name=row.model_name,
            api_base_url=row.api_base_url,
            api_key_is_set=bool(row.api_key_encrypted),
            updated_at=row.updated_at,
        )

    def get_config(self, agent_id: str, organization_id: str) -> AgentConfig:
        with self._connect() as conn:  # noqa: SIM117
            row = self._fetch(conn, agent_id, organization_id)
            if row is None:
                return AgentConfig(
                    agent_id=agent_id,
                    organization_id=organization_id,
                    source=AgentModelSource.STUB,
                    model_name=None,
                    api_base_url=None,
                    api_key_is_set=False,
                    updated_at=datetime.now(UTC),
                )
            return self._to_public(row)

    def list_configs(self, organization_id: str) -> list[AgentConfig]:
        with self._connect() as conn:
            cursor = conn.execute(
                """SELECT agent_id, organization_id, source, model_name, api_base_url,
                          api_key_encrypted, updated_at
                   FROM agent_configs
                   WHERE organization_id = ?
                   ORDER BY agent_id ASC""",
                (organization_id,),
            )
            seen: list[AgentConfig] = []
            for raw in cursor.fetchall():
                decoded = self._decode_row(raw)
                if decoded:
                    seen.append(self._to_public(decoded))
            return seen

    def update_config(self, agent_id: str, organization_id: str, update: AgentConfigUpdate) -> AgentConfig:
        now_iso = datetime.now(UTC).isoformat()

        with self._connect() as conn:
            prior = self._fetch(conn, agent_id, organization_id)

            merged_base = update.api_base_url if update.api_base_url is not None else (
                prior.api_base_url if prior else None
            )
            merged_model = update.model_name if update.model_name is not None else (prior.model_name if prior else None)

            if update.source == AgentModelSource.STUB:
                merged_base = None

            if update.source == AgentModelSource.CUSTOM and not (merged_base or "").strip():
                msg = "CUSTOM cognition exige ``api_base_url`` apontando para endpoint compatível."
                raise ValueError(msg)

            if update.source in {AgentModelSource.OPENAI, AgentModelSource.ANTHROPIC, AgentModelSource.CUSTOM}:
                key_available = update.api_key is not None and update.api_key.strip() != ""
                key_from_prior = bool(prior and prior.api_key_encrypted)
                if not key_available and not key_from_prior:
                    msg = f"Fonte `{update.source.value}` requer ``api_key`` na primeira configuração."
                    raise ValueError(msg)

            encrypted_token: bytes | None
            if update.source == AgentModelSource.STUB:
                encrypted_token = None
            elif update.api_key is not None:
                encrypted_token = self._encrypt_key(update.api_key.strip() or None)
            else:
                encrypted_token = prior.api_key_encrypted if prior else None

            conn.execute(
                """INSERT INTO agent_configs (
                        agent_id, organization_id, source, model_name,
                        api_key_encrypted, api_base_url, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(agent_id, organization_id) DO UPDATE SET
                        source = excluded.source,
                        model_name = excluded.model_name,
                        api_key_encrypted = excluded.api_key_encrypted,
                        api_base_url = excluded.api_base_url,
                        updated_at = excluded.updated_at
                """,
                (
                    agent_id,
                    organization_id,
                    update.source.value,
                    merged_model,
                    encrypted_token,
                    merged_base,
                    now_iso,
                ),
            )
            conn.commit()

            refreshed = self._fetch(conn, agent_id, organization_id)
            if refreshed is None:
                msg = "Persistência de configuração falhou inesperadamente."
                raise RuntimeError(msg)
            return self._to_public(refreshed)

    def resolve_executor(self, agent_id: str, organization_id: str) -> MissionAgentExecutor | None:
        """Return tenant-specific executor or ``None`` to defer to the static registry."""

        with self._connect() as conn:
            row = self._fetch(conn, agent_id, organization_id)
            if row is None:
                return None

            key_plain = self._decrypt_key(row.api_key_encrypted)

            if row.source == AgentModelSource.STUB:
                return DeterministicStubMissionExecutor(agent_binding=agent_id)

            if row.source == AgentModelSource.OLLAMA:
                base = (row.api_base_url or DEFAULT_OLLAMA_V1_BASE).rstrip("/")
                model = row.model_name or "llama3.2"
                token = key_plain or "ollama"
                return OpenAICompatibleMissionExecutor(
                    agent_binding=agent_id,
                    api_key=token,
                    base_url=base,
                    model=model,
                )

            if row.source == AgentModelSource.OPENAI:
                if not key_plain:
                    return None
                base = (row.api_base_url or DEFAULT_OPENAI_BASE).rstrip("/")
                model = row.model_name or "gpt-4o-mini"
                return OpenAICompatibleMissionExecutor(
                    agent_binding=agent_id,
                    api_key=key_plain,
                    base_url=base,
                    model=model,
                )

            if row.source == AgentModelSource.ANTHROPIC:
                if not key_plain:
                    return None
                base = (row.api_base_url or DEFAULT_ANTHROPIC_BASE).rstrip("/")
                model = row.model_name or "claude-3-5-sonnet-20241022"
                return AnthropicMessagesMissionExecutor(
                    agent_binding=agent_id,
                    api_key=key_plain,
                    model=model,
                    api_base_url=base,
                )

            if row.source == AgentModelSource.CUSTOM:
                if not key_plain or not row.api_base_url:
                    return None
                base = row.api_base_url.rstrip("/")
                model = row.model_name or "local-model"
                return OpenAICompatibleMissionExecutor(
                    agent_binding=agent_id,
                    api_key=key_plain,
                    base_url=base,
                    model=model,
                )

        return None

    def effective_hdr_agent(self, definition: AgentDefinition, agent_id: str, organization_id: str) -> tuple[str, str]:
        """Return ``(model, version)`` labels minted into HDR artefacts."""

        with self._connect() as conn:
            row = self._fetch(conn, agent_id, organization_id)
            if row is None:
                return definition.model, definition.version

            model = row.model_name or definition.model
            version = f"{row.source.value}"
            if row.model_name:
                version = f"{row.source.value}:{row.model_name}"
            return model, version

    async def run_smoke_probe(self, agent_id: str, organization_id: str) -> dict[str, str | None]:
        """Invoke a lightweight synthetic node for connectivity validation."""

        executor = self.resolve_executor(agent_id, organization_id)
        if executor is None:
            return {"status": "error", "detail": "Sem executor configurado — reverte para registo estático."}

        dummy = DAGNode(
            node_id="connectivity-probe",
            agent_id=agent_id,
            action="connectivity_probe",
            description="Synthetic connectivity probe",
            input_schema={},
            depends_on=[],
        )
        try:
            outcome = await executor.execute(
                node=dummy,
                mission_id="probe_mission",
                plan_description="Connectivity probe",
                chunk_cost=0.0,
                authorized_tools=[agent_id],
                context={"probe": True},
            )
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "detail": str(exc)[:2048]}

        return {
            "status": "ok",
            "execution_status": outcome.execution_status,
            "cognitive_excerpt": (outcome.cognitive_result or "")[:280],
        }
