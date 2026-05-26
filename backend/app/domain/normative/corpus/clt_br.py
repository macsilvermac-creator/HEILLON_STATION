"""Consolidação das Leis do Trabalho — Decreto-Lei 5.452/1943 + reformas.

Foco em deveres do empregador no uso de IA para gestão de pessoal (art. 444,
não-discriminação), monitoramento eletrônico de trabalhadores e proteção contra
decisões automatizadas em processos seletivos e disciplinares.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.normative.framework_models import (
    FrameworkArticle,
    FrameworkType,
    NormativeFramework,
)

CLT_BR_FRAMEWORK = NormativeFramework(
    framework_id="CLT-BR-1943",
    name="Consolidação das Leis do Trabalho — DL 5.452/1943",
    type=FrameworkType.LAW,
    jurisdiction="BR",
    version="reforma-2017",
    effective_date=datetime(1943, 5, 1, tzinfo=timezone.utc),
    description=(
        "Consolidação das Leis do Trabalho brasileira. Para fins de auditoria de IA: "
        "regula contratação, processos seletivos e disciplinares onde o uso de IA é "
        "submetido a princípios de não-discriminação (arts. 5º CF e 3º §4º CLT) e "
        "à fiscalização do MPT. Aplicação direta a triagem de currículos por IA, "
        "monitoramento eletrônico de jornada e decisões disciplinares assistidas."
    ),
    articles=[
        FrameworkArticle(
            article_id="Art. 5º CF / Art. 3º §4º CLT",
            title="Não-discriminação em triagem por IA",
            text_summary=(
                "É proibida qualquer prática discriminatória limitativa para efeito de acesso à "
                "relação de trabalho ou de sua manutenção. Algoritmos de IA usados em triagem de "
                "currículos, entrevistas automatizadas ou score de candidatos devem ser auditáveis "
                "e demonstrar ausência de viés por gênero, raça, idade, deficiência, orientação "
                "sexual, religião ou origem."
            ),
            compliance_requirements=[
                "Registrar em HDR todo score de candidato gerado por IA com o modelo e versão",
                "Manter explicação técnica disponível (modelo, features, thresholds)",
                "Auditar dataset de treinamento para sinais de viés (auditoria periódica registrada)",
                "Permitir contestação humana de decisão automatizada de não-contratação",
            ],
            hdr_evidence_fields=[
                "agent.model",
                "agent.version",
                "cognitive_snapshot.result",
                "normative.violations",
            ],
        ),
        FrameworkArticle(
            article_id="Art. 482 CLT",
            title="Justa causa — fundamentação humana obrigatória",
            text_summary=(
                "A demissão por justa causa exige fundamentação concreta e humana. Decisões "
                "disciplinares assistidas por IA (ex.: análise de produtividade, monitoramento "
                "eletrônico) só podem subsidiar — nunca substituir — o ato humano de gestor. "
                "TST tem entendimento consolidado sobre nulidade de demissão automatizada."
            ),
            compliance_requirements=[
                "Exigir aprovação humana (gestor identificado) antes de qualquer ato disciplinar",
                "Bloquear emissão automática de notificação de justa causa",
                "Registrar análise de IA como subsídio (cognitive_snapshot) + decisão humana separada",
                "Disponibilizar relatório forense para defesa em eventual reclamatória",
            ],
            hdr_evidence_fields=[
                "user.user_id",
                "user.role",
                "cognitive_snapshot.action",
                "execution.status",
            ],
        ),
        FrameworkArticle(
            article_id="Súmula 342 TST",
            title="Monitoramento eletrônico — limites",
            text_summary=(
                "Súmula 342 TST e jurisprudência consolidada: o monitoramento de empregado por "
                "IA (câmeras inteligentes, análise de produtividade, leitura de e-mails corporativos) "
                "é lícito quando comunicado previamente, proporcional e sem violar intimidade. "
                "Análises de IA sobre comportamento devem ter cadeia de custódia (LGPD + CLT)."
            ),
            compliance_requirements=[
                "Documentar comunicação prévia ao empregado sobre o uso de IA monitora",
                "Limitar coleta ao estritamente necessário (princípio da minimização — LGPD)",
                "Armazenar HDR de cada análise de IA sobre dados do trabalhador",
                "Permitir acesso do empregado aos dados pessoais e análises (LGPD art. 18)",
            ],
            hdr_evidence_fields=[
                "intent.description",
                "normative.checked",
                "normative.corpus_version",
            ],
        ),
    ],
)
