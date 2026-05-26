"""OAB Recomendação 001/2024 — Uso de IA na Advocacia Brasileira."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

OAB_REC001_FRAMEWORK = NormativeFramework(
    framework_id="OAB-REC001-2024",
    name="OAB Recomendação nº 001/2024 — IA na Advocacia",
    type=FrameworkType.REGULATION,
    jurisdiction="BR",
    version="001/2024",
    effective_date=datetime(2024, 3, 1, tzinfo=timezone.utc),
    description=(
        "Recomendação do Conselho Federal da Ordem dos Advogados do Brasil sobre o uso ético e "
        "responsável de Inteligência Artificial na advocacia. Estabelece diretrizes para uso de IA "
        "em pesquisa jurídica, elaboração de peças e aconselhamento ao cliente, com ênfase na "
        "responsabilidade do advogado pela revisão e validação de conteúdo gerado por IA."
    ),
    articles=[
        FrameworkArticle(
            article_id="§ 2 OAB/001",
            title="Responsabilidade do advogado por conteúdo gerado por IA",
            text_summary=(
                "O advogado permanece integralmente responsável por todo conteúdo jurídico produzido "
                "com auxílio de IA, devendo revisar, validar e assinar pessoalmente quaisquer peças "
                "processuais ou pareceres gerados. Não é permitida a delegação da responsabilidade "
                "profissional ao sistema de IA."
            ),
            compliance_requirements=[
                "Exigir revisão e assinatura humana de advogado inscrito em todas as peças",
                "Registrar advogado responsável (OAB/UF número) nos metadados da missão",
                "Proibir submissão autônoma de peças sem aprovação humana do advogado",
            ],
            hdr_evidence_fields=[
                "cognitive_snapshot.action",
                "cognitive_snapshot.result",
                "normative.checked",
            ],
        ),
        FrameworkArticle(
            article_id="§ 4 OAB/001",
            title="Sigilo profissional e dados dos clientes",
            text_summary=(
                "O advogado não pode inserir em sistemas de IA externos informações confidenciais "
                "de clientes que possam comprometer o sigilo profissional previsto no Estatuto da "
                "OAB (Lei 8.906/94, art. 7º, XIX). Dados de clientes só podem ser processados em "
                "sistemas com garantias adequadas de confidencialidade e não-treinamento."
            ),
            compliance_requirements=[
                "Proibir envio de dados identificáveis de clientes a LLMs externos sem data processing agreement",
                "Verificar que o modelo em uso garante não-treinamento com dados dos clientes",
                "Aplicar anonimização antes de processar dados de clientes em IA",
            ],
            hdr_evidence_fields=[
                "normative.violations",
                "intent.description",
                "agent.model",
            ],
        ),
        FrameworkArticle(
            article_id="§ 6 OAB/001",
            title="Citação de jurisprudência e prevenção de alucinações",
            text_summary=(
                "O advogado deve verificar toda citação de jurisprudência ou doutrina gerada por IA "
                "antes de utilizá-la em peças processuais. É vedada a apresentação de decisões ou "
                "obras inventadas (alucinações de IA) como fonte jurídica real. A verificação deve "
                "ser feita nas bases oficiais (TJSP, STJ, STF, etc.)."
            ),
            compliance_requirements=[
                "Verificar toda citação jurisprudencial em base oficial antes de uso em peça",
                "Registrar verificação humana de citações (citation_verified=True) no HDR",
                "Implementar detecção de alucinações no fluxo de geração de peças jurídicas",
            ],
            hdr_evidence_fields=[
                "cognitive_snapshot.result",
                "normative.violations",
                "execution.status",
            ],
        ),
    ],
)
