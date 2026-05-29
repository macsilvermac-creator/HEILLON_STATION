"""Domain models for the privacy bounded context (LGPD Fase 14)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ─── Enums ────────────────────────────────────────────────────────────────────


class LegalBasis(str, Enum):
    """LGPD art. 7 bases legais de tratamento."""

    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    LEGITIMATE_INTEREST = "legitimate_interest"
    VITAL_INTEREST = "vital_interest"
    PUBLIC_TASK = "public_task"


class DPORequestType(str, Enum):
    """LGPD art. 18 direitos do titular."""

    ACCESS = "access"
    CORRECTION = "correction"
    DELETION = "deletion"
    PORTABILITY = "portability"
    REVOCATION = "revocation"
    INFO = "info"


class DPORequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class RIPDStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


class IncidentCategory(str, Enum):
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_LEAK = "data_leak"
    RANSOMWARE = "ransomware"
    INSIDER_THREAT = "insider_threat"
    LOST_DEVICE = "lost_device"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    EVALUATING = "evaluating"
    ANPD_NOTIFIED = "anpd_notified"
    SUBJECTS_NOTIFIED = "subjects_notified"
    CLOSED = "closed"


class ConsentPurpose(str, Enum):
    ANALYTICS = "analytics"
    AI_TRAINING = "ai_training"
    MARKETING = "marketing"
    THIRD_PARTY = "third_party"
    RESEARCH = "research"
    CORE_SERVICE = "core_service"  # always granted (legitimate interest / contract)


class LogType(str, Enum):
    APPLICATION = "application"  # Marco Civil: 6 months minimum, 12 months max
    CONNECTION = "connection"  # Marco Civil: 1 year minimum


# ─── RIPD ─────────────────────────────────────────────────────────────────────


class RIPDCreate(BaseModel):
    """Payload for creating a new RIPD report (LGPD art. 38)."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=200)
    processing_type: str = Field(..., description="e.g. ingestion, analysis, forensic")
    legal_basis: LegalBasis
    purpose: str = Field(..., min_length=10)
    data_categories: list[str] = Field(..., min_length=1)
    data_lifecycle: str = Field(..., min_length=10)
    recipients: list[str] = Field(default_factory=list)
    risks_identified: list[str] = Field(default_factory=list)
    safeguards: list[str] = Field(default_factory=list)


class RIPDReport(BaseModel):
    """Full RIPD entity as stored."""

    model_config = ConfigDict(extra="forbid")

    ripd_id: str
    organization_id: str
    created_by: str
    title: str
    processing_type: str
    legal_basis: LegalBasis
    purpose: str
    data_categories: list[str]
    data_lifecycle: str
    recipients: list[str]
    risks_identified: list[str]
    safeguards: list[str]
    dpo_name: str
    dpo_email: str
    status: RIPDStatus
    pdf_path: str | None
    pdf_checksum: str | None
    created_at: datetime
    approved_at: datetime | None
    approved_by: str | None


# ─── DPO Requests ─────────────────────────────────────────────────────────────


class DPORequestCreate(BaseModel):
    """Public form submission — no auth required."""

    model_config = ConfigDict(extra="forbid")

    requester_name: str = Field(..., min_length=2, max_length=200)
    requester_email: str = Field(..., description="Contact email")
    requester_cpf: str | None = Field(
        None, description="CPF para verificação de identidade"
    )
    request_type: DPORequestType
    description: str = Field(..., min_length=10, max_length=2000)

    @field_validator("requester_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            msg = "E-mail inválido"
            raise ValueError(msg)
        return v


class DPORequestUpdate(BaseModel):
    """Admin update to a DPO request."""

    model_config = ConfigDict(extra="forbid")

    status: DPORequestStatus | None = None
    assigned_to: str | None = None
    response_notes: str | None = None


class DPORequest(BaseModel):
    """Full DPO request entity."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    organization_id: str
    requester_name: str
    requester_email: str
    requester_cpf: str | None
    request_type: DPORequestType
    description: str
    status: DPORequestStatus
    assigned_to: str | None
    response_notes: str | None
    created_at: datetime
    due_at: datetime
    completed_at: datetime | None
    ip_address: str | None
    user_agent: str | None


class DPOContact(BaseModel):
    """Public DPO contact info (GET /privacy/dpo-contact)."""

    model_config = ConfigDict(extra="forbid")

    dpo_name: str
    dpo_email: str
    organization_name: str
    privacy_policy_url: str
    request_form_url: str


# ─── Security Incidents ───────────────────────────────────────────────────────


class IncidentCreate(BaseModel):
    """Register a new security incident (ANPD Res. 15/2024)."""

    model_config = ConfigDict(extra="forbid")

    category: IncidentCategory
    description: str = Field(..., min_length=20)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    affected_subjects_count: int = Field(0, ge=0)
    affected_data_types: list[str] = Field(default_factory=list)
    potential_harm: str | None = None
    containment_measures: str | None = None


class IncidentUpdate(BaseModel):
    """Advance incident through the workflow."""

    model_config = ConfigDict(extra="forbid")

    status: IncidentStatus | None = None
    anpd_notified_at: datetime | None = None
    anpd_notification_ref: str | None = None
    subjects_notified_at: datetime | None = None
    notification_method: str | None = None
    containment_measures: str | None = None
    remediation_plan: str | None = None


class SecurityIncident(BaseModel):
    """Full incident entity."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str
    organization_id: str
    detected_at: datetime
    detected_by: str
    category: IncidentCategory
    description: str
    severity: IncidentSeverity
    affected_subjects_count: int
    affected_data_types: list[str]
    potential_harm: str | None
    status: IncidentStatus
    anpd_notification_due_at: datetime | None
    anpd_notified_at: datetime | None
    anpd_notification_ref: str | None
    subjects_notified_at: datetime | None
    notification_method: str | None
    containment_measures: str | None
    remediation_plan: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    closed_by: str | None
    retain_until: datetime
    is_overdue_anpd: bool = (
        False  # computed: anpd_notification_due_at < now and not notified
    )


# ─── Consent ──────────────────────────────────────────────────────────────────


class ConsentUpdate(BaseModel):
    """Set / update consent for a given purpose."""

    model_config = ConfigDict(extra="forbid")

    purpose: ConsentPurpose
    granted: bool


class ConsentRecord(BaseModel):
    """Single consent record for one (user, purpose)."""

    model_config = ConfigDict(extra="forbid")

    consent_id: str
    user_id: str
    organization_id: str
    purpose: ConsentPurpose
    legal_basis: LegalBasis
    granted: bool
    granted_at: datetime | None
    revoked_at: datetime | None
    version: str
    created_at: datetime
    updated_at: datetime


class ConsentBundle(BaseModel):
    """All consent records for a user."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    records: list[ConsentRecord]


# ─── Access log ───────────────────────────────────────────────────────────────


class AccessLogCreate(BaseModel):
    """Internal — record a loggable event."""

    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    organization_id: str = "org_default"
    log_type: LogType = LogType.APPLICATION
    event_type: str
    resource: str | None = None
    ip_address: str = "0.0.0.0"
    user_agent: str | None = None
    response_code: int | None = None


class PurgeStats(BaseModel):
    """Result of a purge run."""

    model_config = ConfigDict(extra="forbid")

    purged_count: int
    purge_cutoff: datetime
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
