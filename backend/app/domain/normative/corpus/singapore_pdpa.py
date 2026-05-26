"""Singapore PDPA + PDPC Advisory Guidelines on AI (2023)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

SINGAPORE_PDPA_FRAMEWORK = NormativeFramework(
    framework_id="SG-PDPA-2012",
    name="Singapore PDPA + PDPC AI Advisory Guidelines (2023)",
    type=FrameworkType.LAW,
    jurisdiction="SG",
    version="2020-amended",
    effective_date=datetime(2021, 2, 1, tzinfo=timezone.utc),
    description=(
        "Personal Data Protection Act 2012 de Singapura, emendado em 2020, combinado com as "
        "Advisory Guidelines on Use of Personal Data in AI Recommendation and Decision Systems "
        "publicadas pelo PDPC em 2023. Regulado pelo Personal Data Protection Commission (PDPC)."
    ),
    articles=[
        FrameworkArticle(
            article_id="§ 13 PDPA",
            title="Limitação de propósito",
            text_summary=(
                "Uma organização pode coletar, usar ou divulgar dados pessoais apenas para fins que "
                "uma pessoa razoável consideraria adequados e que foram notificados ao indivíduo. "
                "Dados coletados para um fim não podem ser usados para outro fim sem novo consentimento "
                "ou base legal adequada."
            ),
            compliance_requirements=[
                "Especificar claramente o propósito de coleta antes da coleta",
                "Não reutilizar dados de treino para outros propósitos sem nova base legal",
                "Registrar purpose_specification nos metadados de cada missão",
            ],
            hdr_evidence_fields=[
                "intent.description",
                "normative.checked",
                "normative.corpus_version",
            ],
        ),
        FrameworkArticle(
            article_id="§ 3 PDPC AI Guidelines",
            title="Transparência em sistemas de recomendação com IA",
            text_summary=(
                "Organizações que usam IA para tomar ou informar decisões que afetam indivíduos "
                "devem ser transparentes sobre o uso de IA, fornecer explicações significativas sobre "
                "decisões automatizadas quando solicitado, e manter documentação sobre o funcionamento "
                "do sistema de IA."
            ),
            compliance_requirements=[
                "Informar usuários quando IA é usada em decisões que os afetam",
                "Fornecer explicação dos principais fatores de decisão automatizada",
                "Manter documentação atualizada do modelo em uso (model card)",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "agent.version",
                "cognitive_snapshot.result",
                "intent.description",
            ],
        ),
        FrameworkArticle(
            article_id="§ 5 PDPC AI Guidelines",
            title="Supervisão humana em sistemas de IA de alto risco",
            text_summary=(
                "Para sistemas de IA que tomam decisões consequenciais (crédito, emprego, habitação, "
                "serviços essenciais), deve haver supervisão humana significativa. Humanos responsáveis "
                "devem ter competência, autoridade e meios para substituir ou modificar decisões de IA."
            ),
            compliance_requirements=[
                "Designar responsável humano para revisão de decisões consequenciais de IA",
                "Garantir que supervisores humanos compreendem as limitações do sistema",
                "Implementar processo documentado de override humano",
            ],
            hdr_evidence_fields=[
                "cognitive_snapshot.action",
                "execution.status",
                "normative.checked",
            ],
        ),
    ],
)
