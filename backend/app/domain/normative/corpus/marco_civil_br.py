"""Marco Civil da Internet — Lei 12.965/2014.

Regula uso da internet no Brasil. Para fins de auditoria de IA: guarda obrigatória
de logs (arts. 13-15), responsabilidade civil de provedores e proteção a dados pessoais
em conexão. Aplicação direta a investigações cibernéticas (Larissa Tavares — PF) e
análises forenses de comunicações.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

MARCO_CIVIL_BR_FRAMEWORK = NormativeFramework(
    framework_id="MARCO-CIVIL-BR-2014",
    name="Marco Civil da Internet — Lei 12.965/2014",
    type=FrameworkType.LAW,
    jurisdiction="BR",
    version="2014",
    effective_date=datetime(2014, 6, 23, tzinfo=timezone.utc),
    description=(
        "Marco Civil da Internet — Lei 12.965/2014. Estabelece princípios, garantias, "
        "direitos e deveres para o uso da internet no Brasil. Define guarda obrigatória "
        "de registros de conexão (1 ano) e de acesso a aplicações (6 meses), com acesso "
        "judicial. Convivência com a LGPD (Lei 13.709/2018)."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 13 MCI",
            title="Guarda de registros de conexão (1 ano)",
            text_summary=(
                "Provedores de conexão à internet devem manter registros de conexão (data, hora, "
                "duração da conexão e endereço IP) por 1 ano, sob sigilo, em ambiente controlado e "
                "de segurança. Análises automatizadas (por IA) sobre esses registros são lícitas "
                "para fins de segurança da rede ou cumprimento de ordem judicial."
            ),
            compliance_requirements=[
                "Registrar em HDR cada acesso de IA ao log de conexão",
                "Manter trilha de ordem judicial autorizadora (judicial_order_id)",
                "Restringir consultas a usuários autorizados (RLS Postgres ativo)",
                "Aplicar criptografia at-rest aos logs (Fernet/at-rest encryption)",
            ],
            hdr_evidence_fields=[
                "user.user_id",
                "intent.description",
                "normative.checked",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 15 MCI",
            title="Guarda de registros de acesso a aplicações (6 meses)",
            text_summary=(
                "Provedor de aplicação organizado profissionalmente deve manter registros de acesso "
                "a aplicações de internet (data, hora, IP do acessante) sob sigilo, em ambiente "
                "controlado, por 6 meses. Plataformas com IA generativa caem nesta hipótese."
            ),
            compliance_requirements=[
                "Manter access_logs por no mínimo 6 meses (CONTEXT: Heillon já cumpre via repository)",
                "Purgar logs após o período via job recorrente",
                "Disponibilizar logs a requisição judicial (ordem do art. 22 MCI)",
            ],
            hdr_evidence_fields=[
                "execution.timestamp_trusted",
                "user.user_id",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 7º X MCI",
            title="Inviolabilidade e sigilo do fluxo de comunicações",
            text_summary=(
                "É assegurada a inviolabilidade e o sigilo do fluxo de suas comunicações pela "
                "internet, salvo por ordem judicial. Análises de IA sobre conteúdo de comunicações "
                "(emails corporativos, mensagens) sem base legal expressa configuram violação. "
                "Quebra de sigilo só por ordem judicial fundamentada (arts. 22-23 MCI)."
            ),
            compliance_requirements=[
                "Bloquear ingestão de comunicações sem registro de base legal (judicial_order ou consentimento)",
                "Documentar autorização em HDR antes de qualquer análise de IA",
                "Rejeitar prompts que peçam análise de conteúdo sigiloso sem fundamento",
                "Aplicar minimização: extrair só campos estritamente necessários",
            ],
            hdr_evidence_fields=[
                "intent.description",
                "normative.violations",
                "execution.status",
            ],
        ),
    ],
)
