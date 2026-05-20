"""Forensic dossier compilers orchestrating deterministic export artefacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.canonical_json import canonical_json_dumps
from app.core import config as runtime_config
from app.core.config import Settings
from app.core.security import generate_hash
from app.domain.forensic.models import AuditManifest, ForensicPackage, ForensicPackageStatus
from app.domain.forensic.pdf_service import render_hdr_lineage_pdf
from app.domain.forensic.repository import ForensicRepository
from app.domain.forensic.signature_service import ForensicManifestSigner
from app.domain.hdr.models import HDR
from app.domain.hdr.repository import HDRRepository
from app.domain.mission.models import MissionStatus
from app.domain.mission.repository import MissionRepository


class ForensicPackageService:
    """Bundles executive PDFs plus JSON lineage, integrity manifests, and detached signatures."""

    def __init__(
        self,
        *,
        settings_provider=None,
        hdr_repository: HDRRepository | None = None,
        mission_repository: MissionRepository | None = None,
        forensic_repository: ForensicRepository | None = None,
    ) -> None:
        self._settings_provider = settings_provider
        self._hdr_repository = hdr_repository or HDRRepository()
        self._mission_repository = mission_repository or MissionRepository()
        self._forensic_repository = forensic_repository or ForensicRepository()

    def _settings(self) -> Settings:
        if self._settings_provider is not None:
            return self._settings_provider()
        return runtime_config.get_settings()

    @staticmethod
    def generate_pdf_report(mission_id: str, hdrs: list[HDR]) -> bytes:
        """Produce deterministic executive summary bytes (plaintext stub preceding PDF/A)."""

        ordered = sorted(hdrs, key=lambda item: item.hdr_id)
        rows = [
            f"{hdr.hdr_id}\t{hdr.hdr_type}\t{hdr.timestamp}\t{hdr.mission_id}" for hdr in ordered
        ]
        header = (
            f"Heillon Legal EASY Forensic Executive Summary — Mission `{mission_id}`\nHDR Count: {len(hdrs)}\n"
        )
        body = "\n".join(rows)
        return (header + body).encode("utf-8")

    @staticmethod
    def generate_json_chain(hdrs: list[HDR]) -> str:
        """Serialize canonical lineage JSON for courthouse technical annexes."""

        lineage = {"mission_lineage": [h.model_dump(mode="json") for h in hdrs]}
        return canonical_json_dumps(lineage)

    @staticmethod
    def compute_package_integrity_hash(*, pdf_checksum: str, json_chain_checksum: str) -> str:
        """Compose SHA-256 integrity token from canonical artefacts (deterministic MVP)."""

        bundle = canonical_json_dumps({"pdf_checksum": pdf_checksum, "json_chain_checksum": json_chain_checksum})
        return generate_hash(bundle.encode("utf-8"))

    def generate_manifest(
        self,
        *,
        package_id: str,
        mission_id: str,
        hdrs: list[HDR],
        generated_by: str,
        integrity_hash: str,
    ) -> AuditManifest:
        """Generate integrity manifest anchored to EASY verification gateways."""

        if not hdrs:
            msg = "Cannot compile manifest without HDR lineage artefacts."
            raise ValueError(msg)
        anchor = hdrs[-1].timestamp.replace("Z", "+00:00")
        generated_at = datetime.fromisoformat(anchor)
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)
        settings = self._settings()
        tail = hdrs[-1].hdr_id
        base = settings.VERIFICATION_PUBLIC_BASE.rstrip("/") or ""
        verification_url = f"{base}/api/v1/verify/{tail}" if base else f"/api/v1/verify/{tail}"
        return AuditManifest(
            package_id=package_id,
            mission_id=mission_id,
            chain_root=hdrs[0].hdr_id,
            chain_tail=tail,
            total_hdrs=len(hdrs),
            generated_at=generated_at,
            generated_by=generated_by,
            integrity_hash=integrity_hash,
            verification_url=verification_url,
        )

    def generate_package(
        self,
        conn,
        mission_id: str,
        *,
        generated_by: str,
    ) -> ForensicPackage:
        """Compile executive artefacts plus detached Ed25519 manifest signatures."""

        mission_plan = self._mission_repository.fetch_plan(conn, mission_id)
        if mission_plan is None:
            msg = "Mission dossier unavailable for forensic export."
            raise ValueError(msg)
        if mission_plan.status != MissionStatus.COMPLETED:
            msg = "Mission must finish execution prior to forensic packaging."
            raise ValueError(msg)

        hdrs = self._hdr_repository.fetch_mission_chain(conn, mission_id)
        if not hdrs:
            msg = "Cannot export forensic dossier without anchored HDR artefacts."
            raise ValueError(msg)

        settings = self._settings()

        json_chain = self.generate_json_chain(hdrs)
        tail = hdrs[-1].hdr_id
        package_slug = generate_hash(f"{mission_id}|{tail}".encode("utf-8"))
        package_id = f"fpkg_{package_slug}"

        dossier_home = settings.FORENSICS_PACKAGE_DIR.resolve() / package_id
        dossier_home.mkdir(parents=True, exist_ok=True)

        if settings.FORENSICS_USE_STUB_PDF:
            pdf_content = self.generate_pdf_report(mission_id, hdrs)
            pdf_filename = "executive_stub.txt"
        else:
            pdf_content = render_hdr_lineage_pdf(
                mission_id=mission_id,
                hdr_sequence=hdrs,
                generated_by=generated_by,
                emitted_iso=hdrs[-1].timestamp,
            )
            pdf_filename = "executive_report.pdf"

        pdf_path = dossier_home / pdf_filename
        json_path = dossier_home / "chain.json"

        pdf_checksum = generate_hash(pdf_content)
        json_chain_checksum = generate_hash(json_chain.encode("utf-8"))
        integrity_hash = self.compute_package_integrity_hash(
            pdf_checksum=pdf_checksum,
            json_chain_checksum=json_chain_checksum,
        )

        anchor = hdrs[-1].timestamp.replace("Z", "+00:00")
        dossier_anchor = datetime.fromisoformat(anchor)
        if dossier_anchor.tzinfo is None:
            dossier_anchor = dossier_anchor.replace(tzinfo=timezone.utc)

        pdf_path.write_bytes(pdf_content)
        json_path.write_text(json_chain, encoding="utf-8")

        manifest = self.generate_manifest(
            package_id=package_id,
            mission_id=mission_id,
            hdrs=hdrs,
            generated_by=generated_by,
            integrity_hash=integrity_hash,
        )

        package = ForensicPackage(
            package_id=package_id,
            mission_id=mission_id,
            status=ForensicPackageStatus.COMPLETED,
            manifest=manifest,
            pdf_checksum=pdf_checksum,
            json_chain_checksum=json_chain_checksum,
            created_at=dossier_anchor,
            download_url=f"/api/v1/forensic/package/{package_id}/download/manifest",
        )

        verification_snapshot = manifest.verification_url

        manifest_digest_bytes = json.dumps(
            manifest.model_dump(mode="json"),
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        signature_absolute: Path | None = None
        try:
            signer = ForensicManifestSigner.from_hex_optional(
                settings.FORENSICS_SIGNATURE_PRIVATE_KEY_HEX,
            )
            signature_target = dossier_home / "manifest_audit.sig"
            signer.write_signature_file(signature_target, manifest_digest_bytes)
            signature_absolute = signature_target.resolve()
        except Exception:
            signature_absolute = None

        self._forensic_repository.insert_completed_package(
            conn,
            package=package,
            pdf_path=str(pdf_path.resolve()),
            json_path=str(json_path.resolve()),
            verification_url_snapshot=verification_snapshot,
            generated_by=generated_by,
            integrity_hash=integrity_hash,
            pdf_checksum=pdf_checksum,
            json_chain_checksum=json_chain_checksum,
            manifest=manifest,
            signature_path=str(signature_absolute) if signature_absolute else None,
        )

        return package
