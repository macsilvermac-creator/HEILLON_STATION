"""UK GDPR — United Kingdom General Data Protection Regulation (post-Brexit)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

UK_GDPR_FRAMEWORK = NormativeFramework(
    framework_id="UK-GDPR-2021",
    name="UK GDPR — Data Protection Act 2018 (amended post-Brexit)",
    type=FrameworkType.LAW,
    jurisdiction="GB",
    version="2021",
    effective_date=datetime(2021, 1, 1, tzinfo=timezone.utc),
    description=(
        "GDPR adaptado ao contexto pós-Brexit do Reino Unido, incorporado ao direito doméstico "
        "pelo European Union (Withdrawal) Act 2018. Regulado pelo ICO (Information Commissioner's "
        "Office). Essencialmente similar ao EU GDPR com adaptações para o ordenamento britânico. "
        "Data adequacy concedida pela UE ao RU em junho 2021."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 22 UK",
            title="Decisões automatizadas incluindo profiling",
            text_summary=(
                "Indivíduos têm direito a não serem sujeitos a decisões baseadas exclusivamente em "
                "tratamento automatizado, incluindo profiling, que produzam efeitos jurídicos ou que "
                "os afetem de forma significativamente similar. Exceções: contrato, lei ou consentimento "
                "explícito — mas sempre com salvaguardas adequadas."
            ),
            compliance_requirements=[
                "Não tomar decisões consequenciais baseadas exclusivamente em IA sem revisão humana",
                "Informar titulares sobre lógica de decisões automatizadas",
                "Implementar direito de contestação de decisões automatizadas",
            ],
            hdr_evidence_fields=[
                "cognitive_snapshot.action",
                "cognitive_snapshot.result",
                "normative.checked",
            ],
        ),
        FrameworkArticle(
            article_id="S.64 DPA2018",
            title="Privacy by design e by default (UK)",
            text_summary=(
                "Controladores devem implementar medidas técnicas e organizativas para assegurar "
                "que, por omissão, apenas dados pessoais necessários para cada finalidade específica "
                "são tratados. Aplica-se à quantidade de dados, extensão do tratamento, período de "
                "conservação e acessibilidade."
            ),
            compliance_requirements=[
                "Implementar minimização de dados em todos os pipelines de IA",
                "Configurar retenção mínima necessária para dados de treino e inferência",
                "Documentar medidas de privacy by design adotadas",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "intent.description",
                "execution.input_hash",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 35 UK",
            title="Avaliação de impacto sobre a proteção de dados (DPIA UK)",
            text_summary=(
                "DPIAs são obrigatórias antes de qualquer tipo de tratamento com elevado risco para "
                "direitos e liberdades, especialmente: profiling sistemático, tratamento em larga "
                "escala de categorias especiais, e monitorização sistemática de espaço acessível ao "
                "público. ICO publica lista de tipos de tratamento que exigem DPIA."
            ),
            compliance_requirements=[
                "Conduzir DPIA para sistemas de IA de alto risco antes do deploy",
                "Consultar ICO quando DPIA identifica alto risco residual",
                "Revisar DPIAs quando há mudança de propósito ou dados",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "normative.corpus_version",
                "intent.description",
            ],
        ),
    ],
)
