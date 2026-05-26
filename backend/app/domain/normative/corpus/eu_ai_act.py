"""EU AI Act (Regulation 2024/1689) — European Union AI governance framework."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

EU_AI_ACT_FRAMEWORK = NormativeFramework(
    framework_id="EU-AI-ACT-2024",
    name="EU AI Act — Regulation (EU) 2024/1689",
    type=FrameworkType.REGULATION,
    jurisdiction="EU",
    version="2024/1689",
    effective_date=datetime(2024, 8, 1, tzinfo=timezone.utc),
    description=(
        "Regulamento europeu que estabelece regras harmonizadas para o desenvolvimento e uso de "
        "Inteligência Artificial, classificando sistemas por nível de risco (inaceitável, alto, "
        "limitado e mínimo) com obrigações proporcionais. Aplicável a partir de agosto de 2026 "
        "para sistemas de alto risco."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 5",
            title="Práticas de IA proibidas",
            text_summary=(
                "São proibidos: sistemas de pontuação social por autoridades públicas, manipulação "
                "subliminar de comportamento humano, exploração de vulnerabilidades (idade, deficiência), "
                "identificação biométrica remota em tempo real em espaços públicos (salvo exceções), "
                "e inferência de emoções em locais de trabalho e ensino."
            ),
            compliance_requirements=[
                "Verificar que o sistema não implementa scoring social",
                "Proibir manipulação comportamental subliminar",
                "Não usar identificação biométrica remota em tempo real sem autorização judicial",
                "Não inferir emoções de funcionários ou estudantes",
            ],
            hdr_evidence_fields=[
                "intent.description",
                "normative.violations",
                "cognitive_snapshot.action",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 9",
            title="Sistema de gestão de risco para IA de alto risco",
            text_summary=(
                "Sistemas de IA de alto risco (Anexo III) devem implementar sistema contínuo de gestão "
                "de risco, incluindo identificação e análise de riscos conhecidos e razoavelmente "
                "previsíveis, adoção de medidas adequadas de gestão, e testes para identificar a "
                "medida de risco mais adequada."
            ),
            compliance_requirements=[
                "Implementar e documentar sistema de gestão de risco (ISO 42001 ou equivalente)",
                "Identificar riscos na fase de design e ao longo do ciclo de vida",
                "Testar sistema com dados representativos antes do deploy",
                "Manter registros de gestão de risco atualizados",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "normative.corpus_version",
                "agent.model",
                "execution.status",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 13",
            title="Transparência e fornecimento de informações",
            text_summary=(
                "Sistemas de IA de alto risco devem ser suficientemente transparentes para permitir que "
                "os usuários interpretem os resultados e os utilizem adequadamente. Deve-se fornecer "
                "documentação técnica, instruções de uso e informações sobre limitações e riscos."
            ),
            compliance_requirements=[
                "Documentar capabilities e limitações do modelo em uso",
                "Registrar versão do modelo e data de treinamento em cada HDR",
                "Fornecer nível de confiança ou incerteza nas saídas quando disponível",
                "Manter Annex IV technical documentation atualizada",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "agent.version",
                "cognitive_snapshot.action",
                "cognitive_snapshot.result",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 14",
            title="Supervisão humana",
            text_summary=(
                "Sistemas de IA de alto risco devem ser projetados para serem efetivamente supervisionados "
                "por pessoas físicas durante o período de uso. Devem permitir que pessoas responsáveis "
                "compreendam as capacidades e limitações, detectem e corrijam anomalias, e substituam ou "
                "interrompam o sistema."
            ),
            compliance_requirements=[
                "Implementar human-in-the-loop para decisões de alto risco",
                "Registrar human_approved antes de atos com efeitos externos",
                "Providenciar mecanismo de override manual para todos os outputs",
                "Logar todas as intervenções humanas no audit trail",
            ],
            hdr_evidence_fields=[
                "cognitive_snapshot.action",
                "execution.status",
                "normative.checked",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 27",
            title="Avaliação de impacto em direitos fundamentais (FRIA)",
            text_summary=(
                "Entidades do setor público e operadores privados de sistemas de IA de alto risco "
                "previstos no Anexo III devem realizar avaliação de impacto nos direitos fundamentais "
                "antes do deployment, documentando riscos identificados e medidas de mitigação."
            ),
            compliance_requirements=[
                "Conduzir FRIA antes do deploy de sistemas de alto risco",
                "Documentar impactos em: não-discriminação, privacidade, dignidade humana",
                "Registrar FRIA_ID em cada missão de alto risco",
                "Revisar FRIA anualmente ou após mudanças significativas no modelo",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "normative.corpus_version",
                "normative.violations",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 50",
            title="Obrigações de transparência para certos sistemas de IA",
            text_summary=(
                "Sistemas de IA que interagem com pessoas naturais devem informar que se trata de "
                "sistema automatizado. Sistemas que geram conteúdo sintético (deepfake, texto gerado) "
                "devem rotular o conteúdo como gerado por IA."
            ),
            compliance_requirements=[
                "Identificar claramente saídas geradas por IA nos relatórios",
                "Rotular conteúdo sintético com metadado AI-generated=True no HDR",
                "Informar ao utilizador quando interage com sistema automatizado",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "cognitive_snapshot.result",
                "intent.description",
            ],
        ),
    ],
)
