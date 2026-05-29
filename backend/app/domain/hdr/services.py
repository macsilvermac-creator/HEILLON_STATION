"""HDR lifecycle orchestration supporting append-only cryptographic custody."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable, Iterable

import httpx

from app.core.canonical_json import canonical_json_dumps
from app.core import config as runtime_config
from app.core.config import Settings
from app.core.security import generate_hdr_id
from app.domain.hdr import timestamp_service
from app.domain.hdr.models import (
    HDR,
    HDRAgent,
    ChainVerificationDetails,
    ChainVerificationResult,
    HDRCognitiveSnapshot,
    HDRExecution,
    HDRIntent,
    HDRNormative,
    HdrTypeLiteral,
    HDRUser,
)


class HDRService:
    """Coordinate immutable HDR generation and audits."""

    def __init__(
        self,
        *,
        settings_provider: Callable[[], Settings] | None = None,
        stamp_client: httpx.Client | None = None,
    ) -> None:
        self._settings_provider = settings_provider
        self._stamp_client = stamp_client

    def _settings(self) -> Settings:
        if self._settings_provider is not None:
            return self._settings_provider()
        return runtime_config.get_settings()

    @staticmethod
    def _issued_at() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    @classmethod
    def _partial_without_trusted(
        cls,
        *,
        hdr_type: HdrTypeLiteral,
        mission_id: str,
        hdr_version: str,
        timestamp: str,
        agent: HDRAgent,
        user: HDRUser,
        intent: HDRIntent,
        execution: HDRExecution,
        cognitive_snapshot: HDRCognitiveSnapshot,
        normative: HDRNormative,
        previous_hdr: str | None,
        supersedes: str | None,
        corrects: str | None,
    ) -> dict[str, object]:
        """JSON payload hashed before stamping `timestamp_trusted`."""

        return {
            "agent": agent.model_dump(mode="json"),
            "cognitive_snapshot": cognitive_snapshot.model_dump(mode="json"),
            "corrects": corrects,
            "execution": execution.model_dump(mode="json"),
            "hdr_type": hdr_type,
            "hdr_version": hdr_version,
            "intent": intent.model_dump(mode="json"),
            "mission_id": mission_id,
            "normative": normative.model_dump(mode="json"),
            "previous_hdr": previous_hdr,
            "supersedes": supersedes,
            "timestamp": timestamp,
            "user": user.model_dump(mode="json"),
        }

    def generate_hdr(
        self,
        *,
        hdr_type: HdrTypeLiteral,
        mission_id: str,
        agent: HDRAgent,
        user: HDRUser,
        intent: HDRIntent,
        execution: HDRExecution,
        cognitive_snapshot: HDRCognitiveSnapshot,
        normative: HDRNormative,
        previous_hdr: str | None = None,
        hdr_version: str = "1.0",
        supersedes: str | None = None,
        corrects: str | None = None,
        timestamp_override: str | None = None,
        allow_stub_fallback: bool | None = None,
    ) -> HDR:
        """Create a stamped HDR sealed with deterministic digests."""

        stamp_settings = self._settings()
        use_stub_fallback = stamp_settings.FORCE_STUB_TIMESTAMP
        if allow_stub_fallback is not None:
            use_stub_fallback = allow_stub_fallback

        issued_at = timestamp_override or self._issued_at()
        preamble = self._partial_without_trusted(
            hdr_type=hdr_type,
            mission_id=mission_id,
            hdr_version=hdr_version,
            timestamp=issued_at,
            agent=agent,
            user=user,
            intent=intent,
            execution=execution,
            cognitive_snapshot=cognitive_snapshot,
            normative=normative,
            previous_hdr=previous_hdr,
            supersedes=supersedes,
            corrects=corrects,
        )
        preamble_bytes = canonical_json_dumps(preamble).encode("utf-8")
        trusted_token = timestamp_service.get_timestamp(
            preamble_bytes,
            settings=self._settings(),
            client=self._stamp_client,
            allow_stub_fallback=use_stub_fallback,
        )

        sealed_body = {**preamble, "timestamp_trusted": trusted_token}
        fingerprint_source = canonical_json_dumps(sealed_body)
        canonical_digest = generate_hdr_id(fingerprint_source)

        return HDR(
            hdr_id=canonical_digest,
            hdr_version=hdr_version,
            hdr_type=hdr_type,
            mission_id=mission_id,
            timestamp=issued_at,
            timestamp_trusted=trusted_token,
            agent=agent,
            user=user,
            intent=intent,
            execution=execution,
            cognitive_snapshot=cognitive_snapshot,
            normative=normative,
            previous_hdr=previous_hdr,
            supersedes=supersedes,
            corrects=corrects,
            canonical_hash=canonical_digest,
        )

    @staticmethod
    def payload_for_digest(hdr: HDR) -> dict[str, object]:
        """JSON mapping excluding cryptographic identifiers."""

        base = hdr.model_dump(mode="json")
        base.pop("hdr_id", None)
        base.pop("canonical_hash", None)
        return base

    @staticmethod
    def imprint_preimage(hdr: HDR) -> bytes:
        """Canonical UTF-8 bytes hashed into the RFC3161 preamble."""

        body = HDRService.payload_for_digest(hdr)
        prelude = dict(body)
        prelude.pop("timestamp_trusted")
        return canonical_json_dumps(prelude).encode("utf-8")

    def verify_single_hdr(self, hdr: HDR) -> bool:
        """Validate digest cohesion and imprint binding."""

        payload = HDRService.payload_for_digest(hdr)
        fingerprint_source = canonical_json_dumps(dict(payload))
        expected_id = generate_hdr_id(fingerprint_source)
        if expected_id != hdr.canonical_hash or hdr.hdr_id != hdr.canonical_hash:
            return False

        preimage = self.imprint_preimage(hdr)
        return timestamp_service.verify_timestamp(preimage, hdr.timestamp_trusted)

    @staticmethod
    def chain_hdr(previous_hdr: HDR, new_hdr: HDR) -> HDR:
        """Assert append-only chaining semantics."""

        if new_hdr.previous_hdr != previous_hdr.hdr_id:
            msg = "Successor HDR must reference predecessor hdr_id."
            raise ValueError(msg)
        return new_hdr

    @staticmethod
    def order_chain(chain: Iterable[HDR]) -> list[HDR]:
        """Return linearized custody respecting singular genesis lineage."""

        records = list(chain)
        if not records:
            return []

        by_id = {hdr.hdr_id: hdr for hdr in records}
        if len(by_id) != len(records):
            msg = "Duplicate hdr_id violates append-only discipline."
            raise ValueError(msg)

        heads = [hdr for hdr in records if hdr.previous_hdr is None]
        if len(heads) != 1:
            msg = "Custody timelines require exactly one genesis HDR."
            raise ValueError(msg)

        followers: dict[str | None, list[HDR]] = {}
        for item in records:
            followers.setdefault(item.previous_hdr, []).append(item)

        ordered: list[HDR] = []
        cursor = heads[0]
        visited: set[str] = set()

        while True:
            if cursor.hdr_id in visited:
                msg = "Circular custody timeline detected."
                raise ValueError(msg)
            visited.add(cursor.hdr_id)
            ordered.append(cursor)

            successors = followers.get(cursor.hdr_id, [])
            if not successors:
                break

            if len(successors) > 1:
                msg = "Branching custody timelines are forbidden in MVP scope."
                raise ValueError(msg)

            cursor = successors[0]

        if len(ordered) != len(records):
            msg = "Detached HDR shards prevent deterministic ordering."
            raise ValueError(msg)

        return ordered

    def verify_chain(self, chain: Iterable[HDR]) -> ChainVerificationResult:
        """Verify every successor binding across the mission lineage."""

        details_steps: list[str] = []

        try:
            ordered = self.order_chain(chain)
        except ValueError as exc:
            details_steps.append(str(exc))
            return ChainVerificationResult(
                valid=False,
                broken_at=0,
                details=ChainVerificationDetails(steps=details_steps),
            )

        for idx, hdr in enumerate(ordered):
            if not self.verify_single_hdr(hdr):
                details_steps.append(f"Integrity failure at index {idx}.")
                return ChainVerificationResult(
                    valid=False,
                    broken_at=idx,
                    details=ChainVerificationDetails(steps=details_steps),
                )

            if idx == 0:
                continue

            if hdr.previous_hdr != ordered[idx - 1].hdr_id:
                details_steps.append(
                    f"Linkage break between indices {idx - 1} and {idx}."
                )
                return ChainVerificationResult(
                    valid=False,
                    broken_at=idx,
                    details=ChainVerificationDetails(steps=details_steps),
                )

        details_steps.append("Append-only lineage verification succeeded.")
        return ChainVerificationResult(
            valid=True, details=ChainVerificationDetails(steps=details_steps)
        )
