"""Colorado SB 205 (2024) — Colorado Artificial Intelligence Act."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

COLORADO_SB205_FRAMEWORK = NormativeFramework(
    framework_id="CO-SB205-2024",
    name="Colorado SB 205 — Artificial Intelligence Act (2024)",
    type=FrameworkType.LAW,
    jurisdiction="US-CO",
    version="SB24-205",
    effective_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
    description=(
        "Colorado Senate Bill 24-205, o primeiro estado americano com lei abrangente de IA. "
        "Exige que developers e deployers de sistemas de IA de alto risco adotem medidas razoáveis "
        "para proteger consumidores de risco algorítmico de discriminação. Vigência: fevereiro 2026."
    ),
    articles=[
        FrameworkArticle(
            article_id="§ 6-1-1702",
            title="Obrigações do deployer de IA de alto risco",
            text_summary=(
                "Deployers de sistemas de IA de alto risco devem: implementar programa de gestão de "
                "risco (NIST AI RMF ou equivalente), realizar avaliações de impacto anuais, notificar "
                "consumidores que uma decisão consequencial foi tomada com IA, e oferecer opt-out ou "
                "apelação humana para decisões consequenciais."
            ),
            compliance_requirements=[
                "Implementar programa de gestão de risco documentado (NIST AI RMF)",
                "Conduzir avaliação de impacto anual para sistemas de alto risco",
                "Notificar consumidores sobre uso de IA em decisões consequenciais",
                "Oferecer mecanismo de apelação humana para decisões automatizadas",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "cognitive_snapshot.action",
                "execution.status",
            ],
        ),
        FrameworkArticle(
            article_id="§ 6-1-1703",
            title="Avaliação de impacto algorítmico",
            text_summary=(
                "Developers devem conduzir avaliações de impacto algorítmico antes do deploy de "
                "sistemas de alto risco, documentando: objetivo e uso pretendido, dados de "
                "treinamento utilizados, métricas de performance por grupo demográfico, riscos "
                "de discriminação identificados e mitigações adotadas."
            ),
            compliance_requirements=[
                "Documentar objetivo e use case pretendido de cada modelo",
                "Registrar proveniência dos dados de treinamento",
                "Medir e documentar performance do modelo por grupo protegido",
                "Registrar avaliação de discriminação algorítmica (AIA_ID)",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "agent.version",
                "normative.corpus_version",
                "intent.description",
            ],
        ),
        FrameworkArticle(
            article_id="§ 6-1-1705",
            title="Direitos do consumidor em decisões consequenciais",
            text_summary=(
                "Consumidores têm direito a: (1) saber quando IA foi usada em decisão consequencial "
                "que lhes afeta, (2) solicitar revisão humana da decisão, (3) recorrer de decisões "
                "adversas, (4) obter explicação sobre os principais fatores que influenciaram a "
                "decisão automatizada."
            ),
            compliance_requirements=[
                "Registrar todas as decisões consequenciais automatizadas com AI_DECISION=True",
                "Disponibilizar explicação dos fatores de decisão ao consumidor",
                "Processar pedidos de revisão humana em prazo razoável",
                "Manter log de apelações e respostas",
            ],
            hdr_evidence_fields=[
                "cognitive_snapshot.action",
                "cognitive_snapshot.result",
                "normative.violations",
            ],
        ),
    ],
)
