"""Código de Processo Penal — Decreto-Lei 3.689/1941 com reformas até Lei 13.964/2019.

Foco na cadeia de custódia de prova digital (arts. 158-A a 158-F, anti-crime package),
na admissibilidade de provas obtidas com auxílio de IA e na proteção contra
nulidades por opacidade algorítmica em investigações policiais.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

CPP_BR_FRAMEWORK = NormativeFramework(
    framework_id="CPP-BR-1941",
    name="Código de Processo Penal — DL 3.689/1941 (Lei 13.964/2019)",
    type=FrameworkType.LAW,
    jurisdiction="BR",
    version="2019-reforma",
    effective_date=datetime(2020, 1, 23, tzinfo=timezone.utc),  # vigência Lei 13.964
    description=(
        "Código de Processo Penal brasileiro, com a reforma do pacote anticrime (Lei "
        "13.964/2019) que codificou a cadeia de custódia de prova material (arts. "
        "158-A a 158-F). Aplicação direta a perícias digitais, OCR forense e qualquer "
        "uso de IA em investigação criminal ou no Ministério Público."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 158-A CPP",
            title="Cadeia de custódia — definição legal",
            text_summary=(
                "Considera-se cadeia de custódia o conjunto de todos os procedimentos utilizados "
                "para manter e documentar a história cronológica do vestígio coletado em locais "
                "ou em vítimas de crimes, para rastrear sua posse e manuseio a partir de seu "
                "reconhecimento até o descarte. Aplicável integralmente a vestígios digitais."
            ),
            compliance_requirements=[
                "Registrar em HDR cada operação sobre o vestígio digital (acesso, leitura, OCR, análise)",
                "Identificar operador responsável (user_id + nome) em cada elo",
                "Marcar timestamp ICP-Brasil em cada etapa relevante",
                "Bloquear acesso a evidência após coleta sem registro em HDR",
            ],
            hdr_evidence_fields=[
                "user.user_id",
                "execution.input_hash",
                "execution.output_hash",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 158-B CPP",
            title="Etapas obrigatórias da cadeia",
            text_summary=(
                "A cadeia de custódia compreende: reconhecimento, isolamento, fixação, coleta, "
                "acondicionamento, transporte, recebimento, processamento, armazenamento e descarte. "
                "Para evidência digital, cada etapa deve gerar um elo HDR distinto, com hash "
                "do estado antes e depois da operação."
            ),
            compliance_requirements=[
                "Mapear cada uma das 10 etapas para um hdr_type apropriado",
                "Gerar input_hash + output_hash em cada etapa que transforma o vestígio (OCR, análise)",
                "Não permitir descarte sem HDR final com timestamp qualificado",
            ],
            hdr_evidence_fields=[
                "hdr_type",
                "execution.input_hash",
                "execution.output_hash",
                "execution.timestamp_trusted",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 158-F CPP",
            title="Quebra da cadeia — consequências",
            text_summary=(
                "O descumprimento da cadeia de custódia pode ensejar a inadmissibilidade da prova. "
                "Em perícia digital com IA, a ausência de HDR rastreável para qualquer transformação "
                "do vestígio (incluindo prompt e modelo) é vetor clássico de nulidade. A defesa pode "
                "arguir quebra; o ônus de demonstrar integridade é da acusação."
            ),
            compliance_requirements=[
                "Manter HDR íntegro do primeiro contato com o vestígio até o relatório final",
                "Disponibilizar relatório forense executivo na fase recursal",
                "Permitir verificação pública da cadeia (/verification/{hdr_id})",
                "Não usar IA em produção de prova sem que HDR cubra todas as etapas",
            ],
            hdr_evidence_fields=[
                "previous_hdr",
                "canonical_hash",
                "normative.checked",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 6º CPP",
            title="Dever da autoridade policial",
            text_summary=(
                "Logo que tiver conhecimento da prática da infração penal, a autoridade policial "
                "deverá dirigir-se ao local, providenciando para que não se alterem o estado e a "
                "conservação das coisas. Em investigações com IA, alterar dados originais (mesmo "
                "para 'limpeza' antes de OCR) sem HDR configura violação."
            ),
            compliance_requirements=[
                "Manter arquivo bruto sem alterações + arquivo processado com HDR separados",
                "Documentar qualquer pré-processamento (limpeza, conversão) em HDR dedicado",
                "Garantir que o hash do arquivo bruto permaneça verificável após análise",
            ],
            hdr_evidence_fields=[
                "execution.input_hash",
                "intent.description",
                "agent.model",
            ],
        ),
    ],
)
