"""Brazil LGPD (Lei 13.709/2018) — first compliance package."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

LGPD_FRAMEWORK = NormativeFramework(
    framework_id="LGPD-BR",
    name="Lei Geral de Proteção de Dados (Lei nº 13.709/2018)",
    type=FrameworkType.LAW,
    jurisdiction="BR",
    version="2018",
    effective_date=datetime(2020, 9, 18, tzinfo=timezone.utc),
    description=(
        "Lei brasileira que dispõe sobre o tratamento de dados pessoais, inclusive nos meios digitais."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 7º",
            title="Bases legais para tratamento de dados pessoais",
            text_summary=(
                "O tratamento de dados pessoais somente poderá ser realizado mediante consentimento, "
                "legítimo interesse, execução de contrato, ou outras bases legais previstas."
            ),
            compliance_requirements=[
                "Identificar a base legal aplicável antes do tratamento",
                "Registrar a base legal utilizada",
                "Comprovar que o tratamento é necessário para a finalidade",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "normative.corpus_version",
                "intent.description",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 6º",
            title="Princípios do tratamento de dados pessoais",
            text_summary=(
                "O tratamento deve observar boa-fé, finalidade, adequação, necessidade, livre acesso, "
                "qualidade, transparência, segurança, prevenção, não discriminação e responsabilização."
            ),
            compliance_requirements=[
                "Demonstrar finalidade específica",
                "Demonstrar adequação (dados proporcionais à finalidade)",
                "Demonstrar necessidade (mínimo de dados possível)",
                "Garantir transparência sobre o tratamento",
            ],
            hdr_evidence_fields=[
                "intent.description",
                "cognitive_snapshot.action",
                "cognitive_snapshot.result",
                "execution.input_hash",
                "execution.output_hash",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 8º",
            title="Consentimento",
            text_summary=(
                "O consentimento deve ser fornecido por escrito ou por outro meio que demonstre a "
                "manifestação de vontade do titular."
            ),
            compliance_requirements=[
                "Comprovar obtenção de consentimento explícito",
                "Registrar finalidade específica do consentimento",
                "Permitir revogação do consentimento",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "normative.violations",
                "intent.description",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 46",
            title="Segurança e sigilo dos dados",
            text_summary=(
                "Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas "
                "aptas a proteger os dados pessoais."
            ),
            compliance_requirements=[
                "Comprovar uso de criptografia para dados em trânsito",
                "Comprovar uso de criptografia para dados em repouso",
                "Registrar medidas de segurança aplicadas",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "agent.version",
                "execution.status",
                "canonical_hash",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 48",
            title="Comunicação de incidentes",
            text_summary=(
                "O controlador deve comunicar à autoridade nacional e ao titular a ocorrência de "
                "incidente de segurança."
            ),
            compliance_requirements=[
                "Registrar qualquer acesso não autorizado a dados",
                "Notificar incidentes em prazo hábil",
                "Documentar medidas de mitigação",
            ],
            hdr_evidence_fields=[
                "normative.violations",
                "execution.status",
            ],
        ),
    ],
)
