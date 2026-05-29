"""Constitutional anchoring — bind HDR custody to normative frameworks (e.g. LGPD)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.hdr.models import HDR
from app.domain.hdr.repository import HDRRepository
from app.domain.normative.compliance_models import (
    ArticleEvidence,
    ComplianceReportSummary,
    FrameworkAnchorBlock,
    HDRAnchorRecord,
)
from app.domain.normative.framework_models import FrameworkArticle, NormativeFramework


def _format_evidence_value(value: object | None) -> str:
    if value is None:
        return ""
    text = str(value)
    return text[:500]


def _field_from_hdr(hdr: HDR, spec: str) -> str:
    """Resolve declarative ``hdr_evidence_fields`` hints to scalar strings."""

    if spec == "normative.checked":
        return _format_evidence_value(hdr.normative.checked)
    if spec == "normative.corpus_version":
        return _format_evidence_value(hdr.normative.corpus_version)
    if spec == "normative.violations":
        return _format_evidence_value(",".join(hdr.normative.violations))
    if spec == "intent.description":
        return _format_evidence_value(hdr.intent.description)
    if spec == "cognitive_snapshot.action":
        return _format_evidence_value(hdr.cognitive_snapshot.action)
    if spec == "cognitive_snapshot.result":
        return _format_evidence_value(hdr.cognitive_snapshot.result)
    if spec == "execution.input_hash":
        return _format_evidence_value(hdr.execution.input_hash)
    if spec == "execution.output_hash":
        return _format_evidence_value(hdr.execution.output_hash)
    if spec == "agent.model":
        return _format_evidence_value(hdr.agent.model)
    if spec == "agent.version":
        return _format_evidence_value(hdr.agent.version)
    if spec == "execution.status":
        return _format_evidence_value(hdr.execution.status)
    if spec == "canonical_hash":
        return _format_evidence_value(hdr.canonical_hash)
    return ""


def _extract_article_evidence(hdr: HDR, article: FrameworkArticle) -> ArticleEvidence:
    fields = {spec: _field_from_hdr(hdr, spec) for spec in article.hdr_evidence_fields}
    return ArticleEvidence(article_id=article.article_id, fields=fields)


class NormativeAnchoringService:
    """Maps HDR payloads to registered frameworks for post-hoc legitimacy proofs."""

    def __init__(self, *, hdr_repository: HDRRepository | None = None) -> None:
        self._hdr = hdr_repository or HDRRepository()
        self._frameworks: dict[str, NormativeFramework] = {}

    def register_framework(self, framework: NormativeFramework) -> None:
        self._frameworks[framework.framework_id] = framework

    def list_frameworks(self) -> list[NormativeFramework]:
        return sorted(self._frameworks.values(), key=lambda f: f.framework_id)

    def get_framework(self, framework_id: str) -> NormativeFramework | None:
        return self._frameworks.get(framework_id)

    def anchor_hdr(
        self, conn, hdr_id: str, framework_ids: list[str]
    ) -> HDRAnchorRecord:
        hdr_model = self._hdr.fetch_hdr(conn, hdr_id)
        if hdr_model is None:
            msg = f"HDR {hdr_id} not found"
            raise ValueError(msg)

        anchor_blocks: list[FrameworkAnchorBlock] = []
        now = datetime.now(timezone.utc)
        for fid in framework_ids:
            framework = self._frameworks.get(fid)
            if framework is None:
                msg = f"Framework {fid} not registered"
                raise ValueError(msg)

            arts = [
                _extract_article_evidence(hdr_model, art) for art in framework.articles
            ]

            anchor_blocks.append(
                FrameworkAnchorBlock(
                    framework_id=framework.framework_id,
                    framework_name=framework.name,
                    articles=arts,
                    anchored_at=now,
                )
            )

        return HDRAnchorRecord(hdr_id=hdr_id, anchors=anchor_blocks)

    def generate_compliance_report(
        self, conn, mission_id: str, framework_id: str
    ) -> ComplianceReportSummary:
        framework = self._frameworks.get(framework_id)
        if framework is None:
            msg = f"Framework {framework_id} not registered"
            raise ValueError(msg)

        hdrs = self._hdr.fetch_mission_chain(conn, mission_id)
        anchored: list[HDRAnchorRecord] = []
        for hdr in hdrs:
            anchored.append(self.anchor_hdr(conn, hdr.hdr_id, [framework_id]))

        compliant = sum(1 for a in anchored if a.is_fully_compliant())
        return ComplianceReportSummary(
            mission_id=mission_id,
            framework_id=framework.framework_id,
            framework_name=framework.name,
            total_hdrs=len(hdrs),
            compliant_hdrs=compliant,
            hdr_anchors=anchored,
            generated_at=datetime.now(timezone.utc),
        )
