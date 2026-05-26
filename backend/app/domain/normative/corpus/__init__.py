"""Normative corpus — all registered legal frameworks.

Each sub-module defines a NormativeFramework with real article text_summaries
and compliance requirements mapped to HDR evidence fields.

Import ALL_FRAMEWORKS to register every jurisdiction at once.
"""

from __future__ import annotations

from app.domain.normative.corpus.clt_br import CLT_BR_FRAMEWORK
from app.domain.normative.corpus.cnj_615 import CNJ_615_FRAMEWORK
from app.domain.normative.corpus.colorado_sb205 import COLORADO_SB205_FRAMEWORK
from app.domain.normative.corpus.cpc_br import CPC_BR_FRAMEWORK
from app.domain.normative.corpus.cpp_br import CPP_BR_FRAMEWORK
from app.domain.normative.corpus.eu_ai_act import EU_AI_ACT_FRAMEWORK
from app.domain.normative.corpus.gdpr_eu import GDPR_FRAMEWORK
from app.domain.normative.corpus.iso_42001 import ISO_42001_FRAMEWORK
from app.domain.normative.corpus.lgpd_br import LGPD_FRAMEWORK  # re-export
from app.domain.normative.corpus.marco_civil_br import MARCO_CIVIL_BR_FRAMEWORK
from app.domain.normative.corpus.nbc_tp01_br import NBC_TP01_BR_FRAMEWORK
from app.domain.normative.corpus.oab_rec001 import OAB_REC001_FRAMEWORK
from app.domain.normative.corpus.singapore_pdpa import SINGAPORE_PDPA_FRAMEWORK
from app.domain.normative.corpus.uae_pdpl import UAE_PDPL_FRAMEWORK
from app.domain.normative.corpus.uk_gdpr import UK_GDPR_FRAMEWORK

ALL_FRAMEWORKS = [
    # Brasil — fundacional
    LGPD_FRAMEWORK,
    MARCO_CIVIL_BR_FRAMEWORK,
    CPC_BR_FRAMEWORK,
    CPP_BR_FRAMEWORK,
    CLT_BR_FRAMEWORK,
    # Brasil — regulação setorial
    CNJ_615_FRAMEWORK,
    OAB_REC001_FRAMEWORK,
    NBC_TP01_BR_FRAMEWORK,
    # União Europeia
    EU_AI_ACT_FRAMEWORK,
    GDPR_FRAMEWORK,
    # EUA
    COLORADO_SB205_FRAMEWORK,
    # Padrões globais
    ISO_42001_FRAMEWORK,
    # APAC + Oriente Médio
    UAE_PDPL_FRAMEWORK,
    UK_GDPR_FRAMEWORK,
    SINGAPORE_PDPA_FRAMEWORK,
]

__all__ = [
    "ALL_FRAMEWORKS",
    "LGPD_FRAMEWORK",
    "MARCO_CIVIL_BR_FRAMEWORK",
    "CPC_BR_FRAMEWORK",
    "CPP_BR_FRAMEWORK",
    "CLT_BR_FRAMEWORK",
    "CNJ_615_FRAMEWORK",
    "OAB_REC001_FRAMEWORK",
    "NBC_TP01_BR_FRAMEWORK",
    "EU_AI_ACT_FRAMEWORK",
    "GDPR_FRAMEWORK",
    "COLORADO_SB205_FRAMEWORK",
    "ISO_42001_FRAMEWORK",
    "UAE_PDPL_FRAMEWORK",
    "UK_GDPR_FRAMEWORK",
    "SINGAPORE_PDPA_FRAMEWORK",
]
