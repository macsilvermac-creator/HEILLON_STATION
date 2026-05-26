"""GDPR — Regulation (EU) 2016/679 General Data Protection Regulation."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

GDPR_FRAMEWORK = NormativeFramework(
    framework_id="GDPR-EU-2016",
    name="GDPR — Regulation (EU) 2016/679",
    type=FrameworkType.REGULATION,
    jurisdiction="EU",
    version="2016/679",
    effective_date=datetime(2018, 5, 25, tzinfo=timezone.utc),
    description=(
        "Regulamento Geral sobre a Proteção de Dados da União Europeia. Define princípios, bases "
        "legais, direitos dos titulares e obrigações dos controladores e operadores de dados "
        "pessoais. Aplicável a organizações que tratam dados de residentes na UE, independentemente "
        "da localização do controlador."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 6",
            title="Licitude do tratamento",
            text_summary=(
                "O tratamento só é lícito se e na medida em que se verifique pelo menos uma base legal: "
                "consentimento, contrato, obrigação jurídica, interesses vitais, tarefa pública ou "
                "interesses legítimos do responsável. A base legal deve ser determinada antes do "
                "tratamento e documentada."
            ),
            compliance_requirements=[
                "Identificar e documentar a base legal antes de cada tratamento",
                "Armazenar legal_basis nos metadados do HDR",
                "Não permitir tratamento sem base legal válida registrada",
                "Manter registo de atividades de tratamento (Art. 30)",
            ],
            hdr_evidence_fields=[
                "intent.description",
                "normative.checked",
                "normative.corpus_version",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 17",
            title="Direito ao apagamento ('direito a ser esquecido')",
            text_summary=(
                "O titular dos dados tem o direito de obter do responsável o apagamento dos seus dados "
                "pessoais sem demora injustificada quando: os dados já não são necessários, o titular "
                "retira o consentimento, os dados foram tratados ilicitamente, ou há obrigação jurídica "
                "de apagamento."
            ),
            compliance_requirements=[
                "Implementar mecanismo de erasure request dentro de 30 dias",
                "Registrar pedidos de apagamento e sua resposta no privacy domain",
                "Verificar se existem obrigações legais de retenção antes do apagamento",
            ],
            hdr_evidence_fields=[
                "normative.violations",
                "execution.status",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 25",
            title="Proteção de dados desde a concepção e por omissão",
            text_summary=(
                "O responsável aplica medidas técnicas e organizativas adequadas para dar execução aos "
                "princípios de proteção de dados de modo eficaz (privacy by design). Por omissão, "
                "apenas os dados pessoais necessários para a finalidade específica são tratados "
                "(privacy by default)."
            ),
            compliance_requirements=[
                "Aplicar minimização de dados em todos os modelos de IA",
                "Configurar privacy_by_default=True em todas as missões que tratem dados pessoais",
                "Documentar medidas técnicas de pseudonimização quando aplicável",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "intent.description",
                "execution.input_hash",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 33",
            title="Notificação de violação de dados pessoais à autoridade de controlo",
            text_summary=(
                "Em caso de violação de dados pessoais, o responsável notifica a autoridade de controlo "
                "competente sem demora injustificada e, sempre que possível, 72 horas após ter tido "
                "conhecimento da mesma. A notificação descreve a natureza da violação, categorias e "
                "número aproximado de titulares afetados."
            ),
            compliance_requirements=[
                "Detetar e registrar violações de dados imediatamente",
                "Notificar DPA dentro de 72 horas de violações de dados pessoais",
                "Manter registro de todas as violações (incluindo as não notificáveis)",
            ],
            hdr_evidence_fields=[
                "normative.violations",
                "execution.status",
                "canonical_hash",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 35",
            title="Avaliação de impacto sobre a proteção de dados (DPIA)",
            text_summary=(
                "Quando um tipo de tratamento, em particular com recurso a novas tecnologias, for "
                "suscetível de implicar um elevado risco para os direitos e liberdades, o responsável "
                "realiza uma avaliação do impacto das operações de tratamento previstas sobre a proteção "
                "de dados pessoais (DPIA)."
            ),
            compliance_requirements=[
                "Conduzir DPIA para tratamentos com alto risco, especialmente com IA",
                "Documentar DPIA_ID nos metadados da missão",
                "Consultar DPO antes do deploy de novos modelos que tratem dados sensíveis",
            ],
            hdr_evidence_fields=[
                "normative.checked",
                "normative.corpus_version",
                "intent.description",
            ],
        ),
    ],
)
