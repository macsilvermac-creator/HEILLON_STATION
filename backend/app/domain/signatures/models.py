"""Universal document signature lifecycle models — cross-jurisdiction."""

from __future__ import annotations

from enum import Enum


class SignatureJurisdiction(str, Enum):
    BR = "BR"
    EU = "EU"
    US = "US"
    UAE = "UAE"
    GLOBAL = "GLOBAL"


class SignatureStandard(str, Enum):
    ICP_BRASIL = "ICP-Brasil"
    EIDAS_QES = "eIDAS-QES"
    EIDAS_AES = "eIDAS-AES"
    ESIGN = "ESIGN"
    UAE_PASS = "UAE-PASS"
    SELF_SIGNED = "Self-Signed"


class SignatureLevel(str, Enum):
    QES = "QES"       # Qualified Electronic Signature
    AES = "AES"       # Advanced Electronic Signature
    SES = "SES"       # Simple Electronic Signature
    ADVANCED = "advanced"
    BASIC = "basic"


class SignatureFormat(str, Enum):
    PADES_LTA = "PAdES-LTA"   # PDF — long-term archive
    CADES_LTA = "CAdES-LTA"   # CMS — long-term archive
    XADES_LTA = "XAdES-LTA"   # XML — long-term archive
    JADES = "JAdES"            # JSON
    PKCS7 = "PKCS7"
    RAW = "raw"


class DocumentAction(str, Enum):
    SENT = "sent"          # Enviado pela persona responsável
    DELIVERED = "delivered"  # Entregue (confirmação de recebimento automática)
    RECEIVED = "received"  # Recebido (ack explícito do destinatário)
    SIGNED = "signed"      # Assinado com certificado qualificado
    REJECTED = "rejected"
    REVOKED = "revoked"


class AckAction(str, Enum):
    RECEIVED = "received"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERSIGNED = "countersigned"


# Mapping: standard → default format
STANDARD_DEFAULT_FORMAT: dict[str, str] = {
    SignatureStandard.ICP_BRASIL: SignatureFormat.CADES_LTA,
    SignatureStandard.EIDAS_QES: SignatureFormat.PADES_LTA,
    SignatureStandard.EIDAS_AES: SignatureFormat.PADES_LTA,
    SignatureStandard.ESIGN: SignatureFormat.PADES_LTA,
    SignatureStandard.UAE_PASS: SignatureFormat.PADES_LTA,
    SignatureStandard.SELF_SIGNED: SignatureFormat.RAW,
}

# Legal value by jurisdiction (informative)
SIGNATURE_LEGAL_VALUE: dict[str, dict[str, str]] = {
    SignatureJurisdiction.BR: {
        SignatureLevel.QES: "Equivalente a assinatura reconhecida em cartório (ICP-Brasil A3)",
        SignatureLevel.AES: "Válida para documentos privados (ICP-Brasil A1)",
        SignatureLevel.SES: "Presunção de autoria apenas",
    },
    SignatureJurisdiction.EU: {
        SignatureLevel.QES: "Equivalente a assinatura manuscrita (eIDAS Art. 25.2)",
        SignatureLevel.AES: "Juridicamente vinculante com ônus probatório",
        SignatureLevel.SES: "Valor probatório mínimo",
    },
    SignatureJurisdiction.US: {
        SignatureLevel.AES: "Legalmente vinculante sob ESIGN Act / UETA",
        SignatureLevel.BASIC: "Válida se intenção de assinar demonstrada",
    },
    SignatureJurisdiction.UAE: {
        SignatureLevel.QES: "UAE PASS — nível qualificado (TDRA)",
        SignatureLevel.AES: "Assinatura avançada com certificado TSP aprovado",
    },
}
