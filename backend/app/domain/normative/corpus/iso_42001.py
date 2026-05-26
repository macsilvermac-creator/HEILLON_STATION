"""ISO 42001:2023 — Artificial Intelligence Management System (AIMS)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

ISO_42001_FRAMEWORK = NormativeFramework(
    framework_id="ISO-42001-2023",
    name="ISO/IEC 42001:2023 — AI Management System (AIMS)",
    type=FrameworkType.CERTIFICATION,
    jurisdiction="GLOBAL",
    version="2023",
    effective_date=datetime(2023, 12, 18, tzinfo=timezone.utc),
    description=(
        "Primeiro padrão internacional para Sistemas de Gestão de Inteligência Artificial (AIMS). "
        "Especifica requisitos para estabelecer, implementar, manter e melhorar continuamente um "
        "AIMS. Alinhado com estrutura de alto nível ISO (HLS), compatível com ISO 9001, ISO 27001. "
        "Base para certificação global de organizações que desenvolvem ou usam IA."
    ),
    articles=[
        FrameworkArticle(
            article_id="Cláusula 4",
            title="Contexto da organização e partes interessadas",
            text_summary=(
                "A organização determina as questões externas e internas relevantes, identifica "
                "partes interessadas e seus requisitos, e define o escopo do AIMS. Inclui mapeamento "
                "de sistemas de IA em uso ou desenvolvimento e seus impactos potenciais."
            ),
            compliance_requirements=[
                "Manter inventário atualizado de todos os sistemas de IA em uso",
                "Identificar e documentar partes interessadas e seus requisitos de IA",
                "Definir e documentar escopo formal do AIMS",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "normative.corpus_version",
                "intent.description",
            ],
        ),
        FrameworkArticle(
            article_id="Cláusula 6",
            title="Planejamento — avaliação de risco de IA",
            text_summary=(
                "A organização planeja ações para abordar riscos e oportunidades de IA. Realiza "
                "avaliação de risco identificando riscos inerentes ao uso de IA, probabilidade de "
                "ocorrência, impacto potencial e tratamento. Inclui avaliação de viés algorítmico, "
                "falhas de segurança e impactos adversos."
            ),
            compliance_requirements=[
                "Conduzir avaliação de risco de IA antes do deploy de novos modelos",
                "Registrar risk_assessment_id nos metadados de missões de alto risco",
                "Avaliar explicitamente: viés, privacidade, segurança, transparência",
                "Revisar avaliação de risco após incidentes ou mudanças significativas",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "agent.model",
                "execution.status",
                "normative.violations",
            ],
        ),
        FrameworkArticle(
            article_id="Cláusula 8",
            title="Operação — controles do Annexo A",
            text_summary=(
                "Implementação dos controles do Annexo A de ISO 42001, incluindo: transparência "
                "de dados e modelos, documentação técnica, avaliação de impacto (FRIA), gestão "
                "de incidentes de IA, monitoramento de performance, e gestão de fornecedores "
                "de IA (cadeia de abastecimento de modelos)."
            ),
            compliance_requirements=[
                "Implementar todos os controles aplicáveis do Annexo A",
                "Manter documentação técnica de modelos (model card)",
                "Estabelecer processo de gestão de incidentes de IA",
                "Monitorar performance e drift de modelos em produção",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "agent.version",
                "cognitive_snapshot.action",
                "execution.status",
            ],
        ),
        FrameworkArticle(
            article_id="Cláusula 10",
            title="Melhoria contínua",
            text_summary=(
                "A organização melhora continuamente a adequação, suficiência e eficácia do AIMS. "
                "Trata não-conformidades, implementa ações corretivas e monitora a eficácia das "
                "ações. Inclui revisão gerencial periódica do AIMS e reporte de métricas de IA."
            ),
            compliance_requirements=[
                "Registrar e tratar todas as não-conformidades de IA",
                "Conduzir revisão gerencial do AIMS pelo menos anualmente",
                "Manter registro de melhorias implementadas",
                "Reportar KPIs de IA à alta direção",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "normative.corpus_version",
                "execution.status",
            ],
        ),
    ],
)
