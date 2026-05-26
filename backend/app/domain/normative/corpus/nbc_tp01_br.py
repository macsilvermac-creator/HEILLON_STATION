"""NBC TP 01 — Norma Brasileira de Contabilidade Técnica Pericial (CFC Res. 1.502).

Disciplina perícia contábil judicial, extrajudicial e arbitral. Para fins de auditoria
de IA: regula uso de ferramentas computacionais em laudo pericial, cadeia documental
e responsabilidade técnica do perito-contador (CRC).
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

NBC_TP01_BR_FRAMEWORK = NormativeFramework(
    framework_id="NBC-TP01-BR-2016",
    name="NBC TP 01 — Norma Técnica Pericial Contábil (CFC Res. 1.502)",
    type=FrameworkType.REGULATION,
    jurisdiction="BR",
    version="2016",
    effective_date=datetime(2016, 6, 1, tzinfo=timezone.utc),
    description=(
        "Norma Brasileira de Contabilidade Técnica Pericial editada pelo Conselho Federal "
        "de Contabilidade (CFC) sob Resolução 1.502/2016. Regula a atuação do perito-contador "
        "em perícia judicial, extrajudicial e arbitral. Quando o perito usa IA para análise de "
        "extratos, conciliações ou cálculos financeiros, mantém integral a responsabilidade "
        "técnica e deve documentar metodologia."
    ),
    articles=[
        FrameworkArticle(
            article_id="Item 5 NBC TP 01",
            title="Responsabilidade técnica do perito",
            text_summary=(
                "O perito-contador responde tecnicamente pelo laudo, ainda que utilize ferramentas "
                "computacionais ou IA. A delegação a sistemas automatizados não exime de "
                "responsabilidade civil, criminal e ética perante CRC. Toda análise gerada por IA "
                "deve ser conferida e ratificada pelo perito inscrito."
            ),
            compliance_requirements=[
                "Registrar CRC/UF do perito responsável em todo HDR de laudo pericial",
                "Exigir revisão humana documentada antes de assinar o laudo",
                "Manter trilha auditável de cada cálculo gerado por IA (input, modelo, resultado)",
                "Bloquear emissão automática de laudo sem assinatura do perito",
            ],
            hdr_evidence_fields=[
                "user.user_id",
                "user.role",
                "user.crc_id",
                "cognitive_snapshot.action",
            ],
        ),
        FrameworkArticle(
            article_id="Item 24 NBC TP 01",
            title="Documentação dos papéis de trabalho",
            text_summary=(
                "O perito deve manter papéis de trabalho que documentem os procedimentos adotados, "
                "as evidências obtidas e as conclusões alcançadas. Quando IA é usada como auxílio, "
                "os artefatos devem incluir: prompt, modelo, versão, parâmetros, output bruto e "
                "interpretação humana. HDR satisfaz integralmente este requisito."
            ),
            compliance_requirements=[
                "Gerar HDR completo para cada análise pericial assistida por IA",
                "Incluir prompt original (intent.description) e resultado bruto (cognitive_snapshot.result)",
                "Documentar model_id, model_version e parâmetros (temperatura, top_p)",
                "Preservar por 5 anos (prazo de arquivamento NBC TP 01) — compatível com WORM",
            ],
            hdr_evidence_fields=[
                "intent.description",
                "agent.model",
                "agent.version",
                "cognitive_snapshot.result",
            ],
        ),
        FrameworkArticle(
            article_id="Item 31 NBC TP 01",
            title="Quesitos e contraditório",
            text_summary=(
                "O laudo deve responder objetivamente aos quesitos formulados pelas partes e pelo "
                "juiz. Análises geradas por IA não respondem quesitos por si só — devem ser "
                "interpretadas pelo perito, que assume a posição técnica. Em contraditório, a "
                "contraparte tem direito a impugnar metodologia e ferramentas usadas."
            ),
            compliance_requirements=[
                "Disponibilizar HDR completo da análise em caso de impugnação",
                "Permitir verificação pública (/verification/{hdr_id}) para defesa",
                "Manter modelo e versão verificáveis (não pode ser modelo descontinuado sem fallback)",
                "Documentar limitações conhecidas do modelo no relatório forense",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "agent.version",
                "normative.checked",
                "normative.violations",
            ],
        ),
    ],
)
