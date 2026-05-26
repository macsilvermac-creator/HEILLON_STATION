"""UAE PDPL — Federal Decree-Law No. 45 of 2021 on Personal Data Protection."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

UAE_PDPL_FRAMEWORK = NormativeFramework(
    framework_id="UAE-PDPL-2021",
    name="UAE PDPL — Federal Decree-Law No. 45/2021",
    type=FrameworkType.LAW,
    jurisdiction="AE",
    version="45/2021",
    effective_date=datetime(2022, 1, 2, tzinfo=timezone.utc),
    description=(
        "Lei federal dos Emirados Árabes Unidos de proteção de dados pessoais. Aplica-se ao "
        "tratamento de dados pessoais no âmbito dos EAU, incluindo free zones (exceto DIFC e ADGM "
        "que têm regimes próprios). Prevê Base Authority (UAEDPR) como supervisora nacional."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 4",
            title="Bases legais para tratamento de dados pessoais",
            text_summary=(
                "O tratamento de dados pessoais é lícito quando: o titular forneceu consentimento "
                "explícito, o tratamento é necessário para execução de contrato, cumprimento de "
                "obrigação legal, proteção de interesses vitais, ou interesses legítimos do "
                "controlador que não prevaleçam sobre direitos do titular."
            ),
            compliance_requirements=[
                "Obter consentimento explícito ou documentar base legal alternativa",
                "Registrar legal_basis nos metadados do tratamento",
                "Manter evidência de consentimento obtido",
            ],
            hdr_evidence_fields=[
                "intent.description",
                "normative.checked",
                "normative.corpus_version",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 22",
            title="Transferência internacional de dados",
            text_summary=(
                "A transferência de dados pessoais para fora dos EAU requer que o país destinatário "
                "ofereça nível de proteção adequado, ou que sejam implementadas salvaguardas contratuais "
                "apropriadas. A UAEDPR mantém lista de países com proteção adequada."
            ),
            compliance_requirements=[
                "Verificar adequação do país destinatário antes de transferência internacional",
                "Documentar safeguards contratuais quando país não tem adequação formal",
                "Registrar transferências internacionais no registro de tratamento",
            ],
            hdr_evidence_fields=[
                "normative.violations",
                "intent.description",
                "execution.status",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 16",
            title="Direitos dos titulares de dados",
            text_summary=(
                "Os titulares têm direito a: acesso aos seus dados pessoais, retificação de dados "
                "inexatos, apagamento quando não mais necessários, portabilidade dos dados, e "
                "oposição ao tratamento para fins de marketing direto. Pedidos devem ser respondidos "
                "em 30 dias."
            ),
            compliance_requirements=[
                "Processar pedidos de acesso, retificação e apagamento em 30 dias",
                "Implementar portabilidade de dados em formato legível por máquina",
                "Registrar e responder pedidos de oposição ao marketing",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "execution.status",
            ],
        ),
    ],
)
