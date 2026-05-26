"""Corpus normativo completo — seed multi-jurisdição para FTS5.

Contém 50+ NormativeRules derivadas de leis e regulamentos reais:
  - LGPD (BR) — Lei 13.709/2018
  - CNJ 615/2025 (BR)
  - OAB Rec. 001/2024 (BR)
  - EU AI Act 2024/1689 (EU)
  - GDPR 2016/679 (EU)
  - Colorado SB 205 (US-CO)
  - CCPA/CPRA (US-CA)
  - UAE PDPL Decreto 45/2021 (AE)
  - UK GDPR / DPA 2018 (GB)
  - Singapore PDPA + PDPC AI Guidelines (SG)
  - ISO 42001:2023 (GLOBAL)

Chamado automaticamente em init_database() via seed_normative_corpus().
"""

from __future__ import annotations

from app.domain.normative.models import NormativeCategory, NormativeRule, ViolationAction

# ---------------------------------------------------------------------------
# LGPD — Lei 13.709/2018 (Brasil)
# ---------------------------------------------------------------------------
_LGPD_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="LGPD-001",
        name="LGPD: Tratamento sem base legal declarada",
        description="Bloquear tratamento de dados pessoais quando nenhuma base legal for declarada no contexto.",
        category=NormativeCategory.LEGAL,
        condition="Intent envolve dados pessoais e legal_basis não está declarada no contexto (Art. 7º)",
        action_on_violation=ViolationAction.REALIGN,
        priority=98,
    ),
    NormativeRule(
        rule_id="LGPD-002",
        name="LGPD: Transferência internacional sem salvaguardas",
        description="Bloquear transferência transfronteiriça de dados pessoais sem salvaguardas documentadas.",
        category=NormativeCategory.LEGAL,
        condition="Intent envolve transferência internacional e safeguards não estão no contexto (Art. 33)",
        action_on_violation=ViolationAction.BLOCK,
        priority=96,
    ),
    NormativeRule(
        rule_id="LGPD-003",
        name="LGPD: Minimização de dados — excesso de campos",
        description="Avisar quando o volume de campos excede o declarado como necessário.",
        category=NormativeCategory.LEGAL,
        condition="input_field_count excede 2x o necessary_fields threshold declarado",
        action_on_violation=ViolationAction.WARN,
        priority=80,
    ),
    NormativeRule(
        rule_id="LGPD-004",
        name="LGPD: Dados sensíveis sem consentimento explícito",
        description="Bloquear tratamento de dados sensíveis (saúde, origem racial, biometria) sem consentimento explícito.",
        category=NormativeCategory.LEGAL,
        condition="Intent envolve categorias especiais de dados pessoais sem explicit_consent (Art. 11)",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="LGPD-005",
        name="LGPD: Armazenamento sem política de retenção",
        description="Exigir prazo de retenção declarado quando dados pessoais são armazenados.",
        category=NormativeCategory.COMPLIANCE,
        condition="Action é armazenar dados pessoais e retention_period não está no contexto",
        action_on_violation=ViolationAction.REALIGN,
        priority=75,
    ),
    NormativeRule(
        rule_id="LGPD-006",
        name="LGPD: Resposta a titular dentro de 15 dias",
        description="Requisições de titulares (acesso, retificação, exclusão) devem ser respondidas em 15 dias.",
        category=NormativeCategory.COMPLIANCE,
        condition="Pedido de titular em aberto há mais de 15 dias corridos sem resposta registrada",
        action_on_violation=ViolationAction.WARN,
        priority=70,
    ),
    NormativeRule(
        rule_id="LGPD-007",
        name="LGPD: Notificação de incidente ANPD em 72h",
        description="Incidentes de segurança que envolvam dados pessoais devem ser notificados à ANPD em até 72 horas.",
        category=NormativeCategory.COMPLIANCE,
        condition="Incidente de segurança identificado envolvendo dados pessoais sem notificação ANPD registrada",
        action_on_violation=ViolationAction.BLOCK,
        priority=95,
    ),
]

# ---------------------------------------------------------------------------
# CNJ 615/2025 — Conselho Nacional de Justiça (Brasil)
# ---------------------------------------------------------------------------
_CNJ_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="CNJ-001",
        name="CNJ 615: Ato judicial de IA sem cadeia HDR",
        description="Todo ato judicial produzido por IA deve ter cadeia HDR completa e rastreável.",
        category=NormativeCategory.LEGAL,
        condition="Output de IA com efeito judicial sem hdr_id encadeado registrado",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="CNJ-002",
        name="CNJ 615: Ato final sem aprovação humana de magistrado",
        description="Decisões finais com força executória requerem aprovação registrada de magistrado ou serventuário.",
        category=NormativeCategory.LEGAL,
        condition="Ato final de IA sem human_approved=True com identificação de magistrado competente",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="CNJ-003",
        name="CNJ 615: Ausência de verificabilidade pública",
        description="Registros de IA em processos judiciais devem ser verificáveis publicamente via hash criptográfico.",
        category=NormativeCategory.COMPLIANCE,
        condition="HDR de ato judicial sem canonical_hash verificável em endpoint público",
        action_on_violation=ViolationAction.REALIGN,
        priority=90,
    ),
    NormativeRule(
        rule_id="CNJ-004",
        name="CNJ 615: Viés algorítmico em ato judicial",
        description="Sistemas de IA em uso judicial devem ter avaliação de viés documentada antes do deploy.",
        category=NormativeCategory.LEGAL,
        condition="Sistema de IA em uso judicial sem bias_assessment_id registrado",
        action_on_violation=ViolationAction.WARN,
        priority=85,
    ),
]

# ---------------------------------------------------------------------------
# OAB Recomendação 001/2024 (Brasil)
# ---------------------------------------------------------------------------
_OAB_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="OAB-001",
        name="OAB: Peça processual sem revisão humana de advogado",
        description="Peças processuais geradas por IA devem ser revisadas e assinadas por advogado inscrito.",
        category=NormativeCategory.LEGAL,
        condition="Output de IA destinado a peça processual sem oab_reviewer registrado no contexto",
        action_on_violation=ViolationAction.BLOCK,
        priority=98,
    ),
    NormativeRule(
        rule_id="OAB-002",
        name="OAB: Dados de cliente em LLM externo sem DPA",
        description="Dados identificáveis de clientes não podem ser enviados a modelos externos sem Data Processing Agreement.",
        category=NormativeCategory.LEGAL,
        condition="Intent envolve dados de cliente e modelo externo sem data_processing_agreement no contexto",
        action_on_violation=ViolationAction.BLOCK,
        priority=95,
    ),
    NormativeRule(
        rule_id="OAB-003",
        name="OAB: Citação jurisprudencial sem verificação",
        description="Citações de jurisprudência geradas por IA devem ser verificadas em base oficial antes de uso.",
        category=NormativeCategory.COMPLIANCE,
        condition="Peça jurídica contendo citações de IA sem citation_verified=True registrado",
        action_on_violation=ViolationAction.REALIGN,
        priority=88,
    ),
]

# ---------------------------------------------------------------------------
# EU AI Act — Regulation 2024/1689 (União Europeia)
# ---------------------------------------------------------------------------
_EU_AI_ACT_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="EUAIACT-001",
        name="EU AI Act: Prática de IA proibida (Art. 5)",
        description="Bloquear sistemas que implementem pontuação social, manipulação subliminar ou identificação biométrica em tempo real não autorizada.",
        category=NormativeCategory.LEGAL,
        condition="Intent envolve social scoring, manipulação subliminar, ou biometria em tempo real sem autorização judicial",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="EUAIACT-002",
        name="EU AI Act: Sistema de alto risco sem gestão de risco (Art. 9)",
        description="Sistemas de IA de alto risco (Annex III) requerem sistema documentado de gestão de risco.",
        category=NormativeCategory.COMPLIANCE,
        condition="Sistema classificado como alto risco sem risk_management_system_id no contexto",
        action_on_violation=ViolationAction.REALIGN,
        priority=92,
    ),
    NormativeRule(
        rule_id="EUAIACT-003",
        name="EU AI Act: Ausência de supervisão humana em decisão de alto risco (Art. 14)",
        description="Sistemas de IA de alto risco devem ter supervisão humana efetiva antes de atos com efeitos externos.",
        category=NormativeCategory.LEGAL,
        condition="Decisão de alto risco executada sem human_oversight_confirmed=True no contexto",
        action_on_violation=ViolationAction.BLOCK,
        priority=95,
    ),
    NormativeRule(
        rule_id="EUAIACT-004",
        name="EU AI Act: FRIA não realizada antes de deploy de alto risco (Art. 27)",
        description="Sistemas de alto risco no setor público requerem avaliação de impacto em direitos fundamentais.",
        category=NormativeCategory.COMPLIANCE,
        condition="Deploy de sistema de alto risco no setor público sem fria_id registrado",
        action_on_violation=ViolationAction.REALIGN,
        priority=88,
    ),
    NormativeRule(
        rule_id="EUAIACT-005",
        name="EU AI Act: Falta de transparência sobre uso de IA (Art. 50)",
        description="Usuários que interagem com IA devem ser informados que estão interagindo com sistema automatizado.",
        category=NormativeCategory.COMPLIANCE,
        condition="Interação com usuário via IA sem disclosure de sistema automatizado",
        action_on_violation=ViolationAction.WARN,
        priority=75,
    ),
    NormativeRule(
        rule_id="EUAIACT-006",
        name="EU AI Act: Documentação técnica Annex IV ausente",
        description="Sistemas de alto risco devem manter documentação técnica completa conforme Annex IV.",
        category=NormativeCategory.COMPLIANCE,
        condition="Sistema de alto risco sem annex_iv_documentation_id registrado",
        action_on_violation=ViolationAction.WARN,
        priority=70,
    ),
]

# ---------------------------------------------------------------------------
# GDPR — Regulation (EU) 2016/679
# ---------------------------------------------------------------------------
_GDPR_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="GDPR-001",
        name="GDPR: Tratamento sem base legal (Art. 6)",
        description="Bloquear tratamento de dados pessoais de residentes da UE sem base legal válida.",
        category=NormativeCategory.LEGAL,
        condition="Intent envolve dados pessoais de residentes UE e lawful_basis não declarada no contexto",
        action_on_violation=ViolationAction.BLOCK,
        priority=98,
    ),
    NormativeRule(
        rule_id="GDPR-002",
        name="GDPR: Decisão automatizada com efeitos jurídicos sem salvaguardas (Art. 22)",
        description="Decisões baseadas exclusivamente em processamento automatizado com efeitos jurídicos requerem salvaguardas.",
        category=NormativeCategory.LEGAL,
        condition="Decisão automatizada com efeitos jurídicos sem revisão humana ou consentimento explícito UE",
        action_on_violation=ViolationAction.REALIGN,
        priority=93,
    ),
    NormativeRule(
        rule_id="GDPR-003",
        name="GDPR: Violação de dados sem notificação DPA em 72h (Art. 33)",
        description="Violações de dados pessoais de residentes UE devem ser notificadas à DPA competente em 72 horas.",
        category=NormativeCategory.COMPLIANCE,
        condition="Violação de dados pessoais de residentes UE sem notificação DPA dentro de 72 horas",
        action_on_violation=ViolationAction.BLOCK,
        priority=96,
    ),
    NormativeRule(
        rule_id="GDPR-004",
        name="GDPR: DPIA não realizada para tratamento de alto risco (Art. 35)",
        description="Tratamentos de alto risco com IA exigem DPIA documentada antes da implementação.",
        category=NormativeCategory.COMPLIANCE,
        condition="Tratamento de alto risco (biometria, monitoramento sistemático, IA) sem dpia_id registrado",
        action_on_violation=ViolationAction.REALIGN,
        priority=87,
    ),
    NormativeRule(
        rule_id="GDPR-005",
        name="GDPR: Transferência internacional sem adequação ou garantias (Art. 44)",
        description="Transferências de dados para países fora da UE sem decisão de adequação ou garantias adequadas são proibidas.",
        category=NormativeCategory.LEGAL,
        condition="Transferência de dados UE para país terceiro sem adequacy_decision ou SCCs documentadas",
        action_on_violation=ViolationAction.BLOCK,
        priority=97,
    ),
]

# ---------------------------------------------------------------------------
# Colorado SB 205 (EUA — Colorado)
# ---------------------------------------------------------------------------
_COLORADO_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="CO-SB205-001",
        name="Colorado SB 205: Decisão consequencial sem notificação ao consumidor",
        description="Deployers devem notificar consumidores quando IA é usada em decisões consequenciais que os afetam.",
        category=NormativeCategory.COMPLIANCE,
        condition="Decisão consequencial (crédito, emprego, habitação, seguro, educação) tomada por IA sem ai_notification_sent=True",
        action_on_violation=ViolationAction.REALIGN,
        priority=88,
    ),
    NormativeRule(
        rule_id="CO-SB205-002",
        name="Colorado SB 205: Ausência de programa de gestão de risco",
        description="Deployers de IA de alto risco devem implementar programa de gestão de risco (NIST AI RMF ou equivalente).",
        category=NormativeCategory.COMPLIANCE,
        condition="Sistema de alto risco sem risk_management_program_id registrado no contexto",
        action_on_violation=ViolationAction.WARN,
        priority=80,
    ),
    NormativeRule(
        rule_id="CO-SB205-003",
        name="Colorado SB 205: Direito de apelação humana negado",
        description="Consumidores afetados por decisões consequenciais de IA têm direito a revisão humana.",
        category=NormativeCategory.LEGAL,
        condition="Decisão consequencial automatizada sem mecanismo de apelação humana disponível",
        action_on_violation=ViolationAction.REALIGN,
        priority=90,
    ),
]

# ---------------------------------------------------------------------------
# CCPA/CPRA — California Consumer Privacy Act (EUA — Califórnia)
# ---------------------------------------------------------------------------
_CCPA_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="CCPA-001",
        name="CCPA: Venda de dados pessoais sem opt-out",
        description="Consumidores da Califórnia têm direito de opt-out da venda de seus dados pessoais.",
        category=NormativeCategory.LEGAL,
        condition="Intent envolve venda ou compartilhamento de dados de consumidores CA sem opt_out_mechanism implementado",
        action_on_violation=ViolationAction.BLOCK,
        priority=95,
    ),
    NormativeRule(
        rule_id="CCPA-002",
        name="CCPA: Automated Decision Technology (ADMT) sem opt-out",
        description="CPRA exige opt-out para uso de tecnologias de decisão automatizada (ADMT) que afetam consumidores CA.",
        category=NormativeCategory.LEGAL,
        condition="Uso de ADMT que afeta consumidores CA sem admt_opt_out implementado",
        action_on_violation=ViolationAction.REALIGN,
        priority=88,
    ),
    NormativeRule(
        rule_id="CCPA-003",
        name="CCPA: Dados sensíveis sem opt-in explícito",
        description="Categorias especiais de dados (saúde, biometria, geolocalização precisa) requerem opt-in explícito em CA.",
        category=NormativeCategory.LEGAL,
        condition="Tratamento de dados sensíveis de consumidores CA sem explicit_opt_in registrado",
        action_on_violation=ViolationAction.BLOCK,
        priority=97,
    ),
]

# ---------------------------------------------------------------------------
# UAE PDPL — Federal Decree-Law No. 45/2021
# ---------------------------------------------------------------------------
_UAE_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="UAE-001",
        name="UAE PDPL: Tratamento de dados sem consentimento ou base legal",
        description="Bloquear tratamento de dados pessoais nos EAU sem consentimento explícito ou base legal alternativa.",
        category=NormativeCategory.LEGAL,
        condition="Intent envolve dados pessoais de residentes EAU sem consent_or_legal_basis declarado",
        action_on_violation=ViolationAction.BLOCK,
        priority=96,
    ),
    NormativeRule(
        rule_id="UAE-002",
        name="UAE PDPL: Transferência para país sem adequação",
        description="Transferência de dados de residentes EAU para países sem adequação formal requer salvaguardas contratuais.",
        category=NormativeCategory.LEGAL,
        condition="Transferência de dados EAU para país não listado pela UAEDPR como adequado sem SCCs",
        action_on_violation=ViolationAction.BLOCK,
        priority=93,
    ),
    NormativeRule(
        rule_id="UAE-003",
        name="UAE PDPL: Pedido de titular sem resposta em 30 dias",
        description="Pedidos de titulares de dados (acesso, retificação, apagamento) nos EAU devem ser respondidos em 30 dias.",
        category=NormativeCategory.COMPLIANCE,
        condition="Pedido de titular EAU em aberto há mais de 30 dias sem resposta registrada",
        action_on_violation=ViolationAction.WARN,
        priority=72,
    ),
]

# ---------------------------------------------------------------------------
# UK GDPR / Data Protection Act 2018 (Reino Unido)
# ---------------------------------------------------------------------------
_UK_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="UKGDPR-001",
        name="UK GDPR: Decisão automatizada com efeitos legais sem salvaguardas",
        description="Decisões baseadas exclusivamente em IA com efeitos jurídicos sobre residentes UK requerem revisão humana.",
        category=NormativeCategory.LEGAL,
        condition="Decisão automatizada com efeitos jurídicos sobre residente UK sem human_review ou consentimento explícito",
        action_on_violation=ViolationAction.REALIGN,
        priority=93,
    ),
    NormativeRule(
        rule_id="UKGDPR-002",
        name="UK GDPR: Violação de dados sem notificação ICO em 72h",
        description="Violações de dados pessoais de residentes UK devem ser notificadas ao ICO dentro de 72 horas.",
        category=NormativeCategory.COMPLIANCE,
        condition="Violação de dados UK sem notificação ICO registrada dentro de 72 horas",
        action_on_violation=ViolationAction.BLOCK,
        priority=95,
    ),
]

# ---------------------------------------------------------------------------
# Singapore PDPA + PDPC AI Guidelines 2023
# ---------------------------------------------------------------------------
_SG_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="PDPA-001",
        name="PDPA: Coleta de dados sem notificação de propósito",
        description="Organizações em Singapura devem notificar indivíduos sobre o propósito da coleta antes ou durante a coleta.",
        category=NormativeCategory.LEGAL,
        condition="Coleta de dados de residentes SG sem purpose_notification documentada",
        action_on_violation=ViolationAction.REALIGN,
        priority=88,
    ),
    NormativeRule(
        rule_id="PDPA-002",
        name="PDPA: Supervisão humana ausente em decisão de IA consequencial",
        description="PDPC guidelines exigem supervisão humana efetiva em decisões consequenciais de IA (crédito, emprego, etc).",
        category=NormativeCategory.COMPLIANCE,
        condition="Decisão consequencial de IA afetando residente SG sem human_oversight confirmado",
        action_on_violation=ViolationAction.REALIGN,
        priority=85,
    ),
]

# ---------------------------------------------------------------------------
# ISO 42001:2023 — AIMS (Global)
# ---------------------------------------------------------------------------
_ISO42001_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="ISO42001-001",
        name="ISO 42001: Deploy sem avaliação de risco de IA documentada",
        description="ISO 42001 exige avaliação de risco documentada antes do deploy de qualquer sistema de IA.",
        category=NormativeCategory.COMPLIANCE,
        condition="Deploy de sistema de IA sem ai_risk_assessment_id registrado no contexto",
        action_on_violation=ViolationAction.WARN,
        priority=78,
    ),
    NormativeRule(
        rule_id="ISO42001-002",
        name="ISO 42001: Incidente de IA sem registro e tratamento",
        description="ISO 42001 Cláusula 10 exige que todas as não-conformidades e incidentes de IA sejam registrados e tratados.",
        category=NormativeCategory.COMPLIANCE,
        condition="Incidente ou não-conformidade de IA identificado sem incident_id registrado no sistema",
        action_on_violation=ViolationAction.WARN,
        priority=75,
    ),
    NormativeRule(
        rule_id="ISO42001-003",
        name="ISO 42001: Model card ausente para sistema em produção",
        description="Controles do Annexo A de ISO 42001 requerem documentação técnica (model card) para sistemas em produção.",
        category=NormativeCategory.COMPLIANCE,
        condition="Sistema de IA em produção sem model_card_id registrado nos metadados",
        action_on_violation=ViolationAction.WARN,
        priority=70,
    ),
    NormativeRule(
        rule_id="ISO42001-004",
        name="ISO 42001: Revisão gerencial do AIMS não realizada",
        description="ISO 42001 Cláusula 9 exige revisão gerencial anual do AIMS com reporte de métricas.",
        category=NormativeCategory.COMPLIANCE,
        condition="AIMS sem revisão gerencial registrada no último ano",
        action_on_violation=ViolationAction.WARN,
        priority=65,
    ),
]

# ---------------------------------------------------------------------------
# Regras gerais de segurança e acesso (cross-jurisdição)
# ---------------------------------------------------------------------------
_GENERAL_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="LEGAL-001",
        name="Bloquear acesso a material privilegiado advogado-cliente",
        description="Impedir acesso a documentos marcados como privilegiados ou comunicação advogado-cliente.",
        category=NormativeCategory.LEGAL,
        condition="Intent referencia material privilegiado ou attorney-client sem autorização registrada",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="LEGAL-002",
        name="Bloquear processamento de PII sem anonimização",
        description="Bloquear processamento de dados pessoais identificáveis sem controle de anonimização ativado.",
        category=NormativeCategory.LEGAL,
        condition="Intent referencia PII sem anonymization_flag=True no contexto",
        action_on_violation=ViolationAction.BLOCK,
        priority=95,
    ),
    NormativeRule(
        rule_id="LEGAL-003",
        name="Exigir aprovação humana para ações externas",
        description="Comunicações ou publicações externas (publish, send, share) requerem aprovação humana registrada.",
        category=NormativeCategory.COMPLIANCE,
        condition="Ação toca canais externos sem artefato de aprovação judicial registrado",
        action_on_violation=ViolationAction.REALIGN,
        priority=90,
    ),
    NormativeRule(
        rule_id="LEGAL-004",
        name="Bloquear ações fora do escopo autorizado",
        description="Bloquear intents que inferem toolchain fora do catálogo authorized_tools sancionado.",
        category=NormativeCategory.SECURITY,
        condition="Ferramenta ou agente solicitado ausente do payload authorized_tools do contexto",
        action_on_violation=ViolationAction.BLOCK,
        priority=85,
    ),
    NormativeRule(
        rule_id="LEGAL-005",
        name="Aviso de custo elevado de missão",
        description="Emitir aviso consultivo quando custo estimado da missão excede threshold de 100 unidades.",
        category=NormativeCategory.CUSTOM,
        condition="estimated_cost_gas > 100",
        action_on_violation=ViolationAction.WARN,
        priority=10,
    ),
]

# ---------------------------------------------------------------------------
# Brasil — Códigos processuais e legislação setorial (F24C)
# ---------------------------------------------------------------------------
_CPC_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="CPC-001",
        name="CPC art. 5º: Boa-fé objetiva em peças assistidas por IA",
        description=(
            "Peças processuais com auxílio de IA devem ter citações jurisprudenciais verificadas; "
            "alucinações de IA configuram violação do dever de boa-fé."
        ),
        category=NormativeCategory.LEGAL,
        condition="Output de IA usado em peça processual sem citation_verified=True",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="CPC-002",
        name="CPC art. 411: Autenticidade de documento eletrônico",
        description=(
            "Artefatos de IA submetidos como prova devem ter cadeia HDR + selo ICP-Brasil "
            "para autenticidade aceitável em juízo."
        ),
        category=NormativeCategory.COMPLIANCE,
        condition="Documento eletrônico submetido sem hdr_id encadeado e selo qualificado",
        action_on_violation=ViolationAction.REALIGN,
        priority=92,
    ),
    NormativeRule(
        rule_id="CPC-003",
        name="CPC art. 158-A: Cadeia de custódia analógica em prova digital",
        description=(
            "Vestígios digitais usados em processo civil seguem cadeia de custódia análoga ao CPP."
        ),
        category=NormativeCategory.LEGAL,
        condition="Transformação de evidência sem HDR registrando operador e timestamps",
        action_on_violation=ViolationAction.BLOCK,
        priority=98,
    ),
]

_CPP_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="CPP-001",
        name="CPP art. 158-A: Cadeia de custódia de vestígio digital",
        description=(
            "Toda operação sobre vestígio digital (acesso, OCR, análise por IA) deve gerar HDR."
        ),
        category=NormativeCategory.LEGAL,
        condition="Operação sobre vestígio criminal sem HDR identificando operador e timestamp",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="CPP-002",
        name="CPP art. 158-B: Etapas obrigatórias documentadas",
        description=(
            "Cada uma das 10 etapas (reconhecimento, isolamento, fixação, coleta, "
            "acondicionamento, transporte, recebimento, processamento, armazenamento, descarte) "
            "deve mapear para um hdr_type."
        ),
        category=NormativeCategory.LEGAL,
        condition="Vestígio digital com etapas em branco na trilha HDR",
        action_on_violation=ViolationAction.WARN,
        priority=90,
    ),
    NormativeRule(
        rule_id="CPP-003",
        name="CPP art. 158-F: Quebra de cadeia → inadmissibilidade",
        description=(
            "Ausência de HDR para qualquer transformação configura risco de nulidade; sistema deve "
            "sinalizar e bloquear submissão em juízo."
        ),
        category=NormativeCategory.LEGAL,
        condition="Tentativa de gerar relatório forense com gap na cadeia HDR",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="CPP-004",
        name="CPP art. 6º: Preservar estado original do vestígio",
        description=(
            "Pré-processamento (limpeza, conversão) do arquivo bruto exige HDR dedicado e "
            "preservação do hash original."
        ),
        category=NormativeCategory.LEGAL,
        condition="Modificação de arquivo bruto sem HDR de pré-processamento separado",
        action_on_violation=ViolationAction.REALIGN,
        priority=92,
    ),
]

_CLT_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="CLT-001",
        name="CLT/CF: Não-discriminação em triagem por IA",
        description=(
            "Algoritmos usados em triagem de candidatos exigem auditoria de viés registrada e "
            "explicabilidade documentada."
        ),
        category=NormativeCategory.LEGAL,
        condition="Score de candidato sem bias_assessment_id e model card documentado",
        action_on_violation=ViolationAction.WARN,
        priority=88,
    ),
    NormativeRule(
        rule_id="CLT-002",
        name="CLT art. 482: Justa causa exige decisão humana",
        description=(
            "Atos disciplinares (advertência, suspensão, demissão por JC) não podem ser "
            "automatizados; gestor humano identificado deve aprovar."
        ),
        category=NormativeCategory.LEGAL,
        condition="Ato disciplinar emitido sem human_approved=True com identificação de gestor",
        action_on_violation=ViolationAction.BLOCK,
        priority=98,
    ),
    NormativeRule(
        rule_id="CLT-003",
        name="Súmula 342 TST: Monitoramento eletrônico — comunicação prévia",
        description=(
            "Análise de IA sobre dados do trabalhador requer comunicação prévia registrada e "
            "minimização de dados."
        ),
        category=NormativeCategory.COMPLIANCE,
        condition="Análise comportamental de IA sem worker_notification_id registrado",
        action_on_violation=ViolationAction.WARN,
        priority=80,
    ),
]

_NBC_TP01_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="NBCTP-001",
        name="NBC TP 01: Responsabilidade técnica do perito-contador",
        description=(
            "Laudo pericial assistido por IA exige assinatura humana com CRC/UF do perito."
        ),
        category=NormativeCategory.LEGAL,
        condition="Laudo pericial submetido sem CRC do perito registrado em HDR",
        action_on_violation=ViolationAction.BLOCK,
        priority=98,
    ),
    NormativeRule(
        rule_id="NBCTP-002",
        name="NBC TP 01: Papéis de trabalho documentados",
        description=(
            "Cada análise de IA usada em perícia deve registrar prompt, modelo, versão, output "
            "bruto e interpretação humana."
        ),
        category=NormativeCategory.COMPLIANCE,
        condition="HDR pericial sem agent.model + agent.version + intent.description preenchidos",
        action_on_violation=ViolationAction.REALIGN,
        priority=90,
    ),
    NormativeRule(
        rule_id="NBCTP-003",
        name="NBC TP 01: Resposta a quesitos requer interpretação humana",
        description=(
            "Análise de IA não responde quesitos por si só; perito assume posição técnica."
        ),
        category=NormativeCategory.LEGAL,
        condition="Resposta a quesito gerada por IA sem revisão humana registrada",
        action_on_violation=ViolationAction.BLOCK,
        priority=95,
    ),
]

_MARCO_CIVIL_RULES: list[NormativeRule] = [
    NormativeRule(
        rule_id="MCI-001",
        name="Marco Civil art. 13: Guarda de registros de conexão (1 ano)",
        description=(
            "Acesso a logs de conexão exige base legal (judicial_order) registrada em HDR."
        ),
        category=NormativeCategory.LEGAL,
        condition="Consulta a log de conexão sem judicial_order_id em HDR",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="MCI-002",
        name="Marco Civil art. 15: Retenção mínima de access_logs (6 meses)",
        description=(
            "Plataformas com IA generativa devem manter access_logs por no mínimo 6 meses."
        ),
        category=NormativeCategory.COMPLIANCE,
        condition="Configuração de purge de access_logs < 6 meses",
        action_on_violation=ViolationAction.WARN,
        priority=80,
    ),
    NormativeRule(
        rule_id="MCI-003",
        name="Marco Civil art. 7º X: Inviolabilidade do fluxo de comunicações",
        description=(
            "Análise de IA sobre comunicações exige base legal expressa (ordem judicial ou "
            "consentimento) registrada antes do processamento."
        ),
        category=NormativeCategory.LEGAL,
        condition="Análise de IA sobre comunicação sem legal_basis registrada em HDR",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
]

# ---------------------------------------------------------------------------
# Corpus completo ordenado por prioridade
# ---------------------------------------------------------------------------
ALL_CORPUS_RULES: tuple[NormativeRule, ...] = tuple(
    sorted(
        _GENERAL_RULES
        + _LGPD_RULES
        + _CNJ_RULES
        + _OAB_RULES
        + _CPC_RULES
        + _CPP_RULES
        + _CLT_RULES
        + _NBC_TP01_RULES
        + _MARCO_CIVIL_RULES
        + _EU_AI_ACT_RULES
        + _GDPR_RULES
        + _COLORADO_RULES
        + _CCPA_RULES
        + _UAE_RULES
        + _UK_RULES
        + _SG_RULES
        + _ISO42001_RULES,
        key=lambda r: r.priority,
        reverse=True,
    )
)

CORPUS_VERSION = "24.0.0"
CORPUS_JURISDICTIONS = ["BR", "EU", "US-CO", "US-CA", "AE", "GB", "SG", "GLOBAL"]
CORPUS_FRAMEWORKS = [
    # Brasil
    "LGPD-BR", "MARCO-CIVIL-BR-2014",
    "CPC-BR-2015", "CPP-BR-1941", "CLT-BR-1943",
    "CNJ-615-2025", "OAB-REC001-2024", "NBC-TP01-BR-2016",
    # Internacional
    "EU-AI-ACT-2024", "GDPR-EU-2016",
    "CO-SB205-2024", "CCPA-CPRA",
    "UAE-PDPL-2021", "UK-GDPR-2021",
    "SG-PDPA-2012", "ISO-42001-2023",
]


def seed_normative_corpus(conn) -> int:
    """Seed all corpus rules into the normative_rules FTS5 table.

    Safe to call multiple times — uses INSERT OR REPLACE (upsert).
    Returns the number of rules seeded.
    """
    from app.domain.normative.fts_repository import seed_corpus  # local import to avoid circular

    seed_corpus(conn, ALL_CORPUS_RULES)
    return len(ALL_CORPUS_RULES)
