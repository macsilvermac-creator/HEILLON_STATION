"""Código de Processo Civil — Lei 13.105/2015 (Brasil).

Foco em provas eletrônicas, prazo, deveres das partes e produção probatória
suscetíveis a uso de IA pelo advogado ou pelo juiz.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

CPC_BR_FRAMEWORK = NormativeFramework(
    framework_id="CPC-BR-2015",
    name="Código de Processo Civil — Lei 13.105/2015",
    type=FrameworkType.LAW,
    jurisdiction="BR",
    version="2015",
    effective_date=datetime(2016, 3, 18, tzinfo=timezone.utc),
    description=(
        "Diploma processual civil brasileiro. Para fins de auditoria de IA: estabelece "
        "deveres de boa-fé e cooperação (arts. 5º e 6º), regula a prova documental "
        "eletrônica (art. 411), a perícia (arts. 156-158-F sobre cadeia de custódia) e "
        "o uso de meios eletrônicos no processo (art. 193). Petições assistidas por IA "
        "permanecem sujeitas a estes deveres."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 5º CPC",
            title="Boa-fé objetiva e veracidade",
            text_summary=(
                "Aquele que de qualquer forma participa do processo deve comportar-se de acordo "
                "com a boa-fé. Petições, alegações e provas geradas com auxílio de IA estão "
                "submetidas a este dever — alucinações, citações falsas e inclusão de "
                "jurisprudência inventada configuram violação."
            ),
            compliance_requirements=[
                "Verificar todas as citações jurisprudenciais antes da peticionar",
                "Registrar no HDR a verificação humana de citações (citation_verified=True)",
                "Bloquear protocolo automatizado se citation_verified == False",
                "Documentar revisão do advogado responsável (OAB/UF inscrição)",
            ],
            hdr_evidence_fields=[
                "cognitive_snapshot.result",
                "normative.checked",
                "normative.violations",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 411 CPC",
            title="Documento eletrônico — autenticidade",
            text_summary=(
                "Documento eletrônico só é admitido como prova se assegurada sua autenticidade. "
                "Para artefatos produzidos com IA, a cadeia de custódia HDR + timestamp ICP-Brasil "
                "satisfaz o requisito quando o relatório forense é apresentado."
            ),
            compliance_requirements=[
                "Gerar relatório forense PDF/A-3 com selo ICP-Brasil para todo artefato submetido",
                "Vincular hdr_id ao documento via metadado embutido",
                "Disponibilizar URL pública de verificação (/verification/{hdr_id})",
                "Preservar canonical_hash em registro independente para impugnação",
            ],
            hdr_evidence_fields=[
                "execution.input_hash",
                "execution.output_hash",
                "normative.corpus_version",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 158-A CPP/CPC analógico",
            title="Cadeia de custódia de prova digital",
            text_summary=(
                "Aplicação analógica dos arts. 158-A a 158-F do CPP (introduzidos pela Lei "
                "13.964/2019) ao processo civil: documentos eletrônicos produzidos com IA devem "
                "ter cadeia de custódia preservada (coleta, acondicionamento, transporte, "
                "recebimento, processamento, armazenamento, descarte) — o HDR cobre cada etapa."
            ),
            compliance_requirements=[
                "HDR.type cobre todos os 7 elos: ingestion, intention, ocr, classification, analysis, mission, violation",
                "Armazenar previous_hdr_id em cada elo para encadeamento",
                "Bloquear remoção/edição de HDR após criação (WORM)",
            ],
            hdr_evidence_fields=[
                "hdr_type",
                "previous_hdr",
                "canonical_hash",
            ],
        ),
    ],
)
