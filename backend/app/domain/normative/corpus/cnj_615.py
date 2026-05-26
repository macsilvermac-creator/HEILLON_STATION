"""CNJ Resolução 615/2025 — Uso de IA no Poder Judiciário Brasileiro."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

CNJ_615_FRAMEWORK = NormativeFramework(
    framework_id="CNJ-615-2025",
    name="CNJ Resolução nº 615/2025 — IA no Poder Judiciário",
    type=FrameworkType.REGULATION,
    jurisdiction="BR",
    version="2025",
    effective_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
    description=(
        "Resolução do Conselho Nacional de Justiça que regulamenta o uso de Inteligência Artificial "
        "no âmbito do Poder Judiciário, exigindo cadeia de custódia, registro de decisões e "
        "supervisão humana em atos com efeitos jurídicos."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 3º",
            title="Rastreabilidade e cadeia de custódia obrigatória",
            text_summary=(
                "Toda aplicação de IA que produza atos com efeitos jurídicos deve manter cadeia de "
                "custódia rastreável, com registro imutável de cada etapa do processamento, "
                "identificação do modelo utilizado, versão, parâmetros e resultado gerado."
            ),
            compliance_requirements=[
                "Manter HDR com hdr_id único para cada ato de IA",
                "Registrar model_id, model_version e executor em cada HDR",
                "Encadear HDRs com previous_hdr_id para rastreabilidade",
                "Armazenar canonical_hash imutável (SHA-256)",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "agent.version",
                "canonical_hash",
                "normative.checked",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 5º",
            title="Supervisão humana obrigatória em decisões finais",
            text_summary=(
                "Decisões judiciais finais baseadas em IA devem ser revisadas e validadas por magistrado "
                "ou serventuário competente. Nenhum ato com força executória pode ser emitido sem "
                "aprovação humana registrada e identificada."
            ),
            compliance_requirements=[
                "Registrar human_approved=True com ID do responsável antes de atos finais",
                "Manter audit log de aprovações humanas no governance domain",
                "Proibir execução autônoma de atos com efeitos jurídicos diretos",
            ],
            hdr_evidence_fields=[
                "cognitive_snapshot.action",
                "cognitive_snapshot.result",
                "execution.status",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 7º",
            title="Verificabilidade pública",
            text_summary=(
                "Os registros de IA utilizados em processos judiciais devem ser verificáveis por "
                "qualquer parte interessada, incluindo advogados, peritos e o Ministério Público, "
                "mediante consulta pública autenticada por hash criptográfico."
            ),
            compliance_requirements=[
                "Disponibilizar endpoint público /verify/{hdr_id} sem autenticação",
                "Incluir timestamp RFC 3161 verificável na cadeia HDR",
                "Gerar pacote forense com chain.json para cada missão concluída",
            ],
            hdr_evidence_fields=[
                "canonical_hash",
                "normative.corpus_version",
                "intent.description",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 9º",
            title="Proibição de viés e discriminação algorítmica",
            text_summary=(
                "É vedado o uso de sistemas de IA que produzam resultados discriminatórios com base "
                "em raça, gênero, orientação sexual, crença religiosa ou condição socioeconômica. "
                "Relatórios de avaliação de impacto devem ser mantidos."
            ),
            compliance_requirements=[
                "Executar avaliação de viés antes do deploy de novos modelos",
                "Registrar FRIA (Fundamental Rights Impact Assessment) para sistemas de alto risco",
                "Auditar outputs periodicamente para detecção de padrões discriminatórios",
            ],
            hdr_evidence_fields=[
                "normative.violations",
                "cognitive_snapshot.action",
            ],
        ),
    ],
)
