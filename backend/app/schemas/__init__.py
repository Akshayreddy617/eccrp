"""
ECCRP Pydantic Schemas
Request/response models for all API endpoints.
"""

from datetime import datetime
from datetime import date
from typing import Optional, List, Any, Dict
from uuid import UUID
import re

from pydantic import BaseModel, EmailStr, validator, Field
from app.db.models import UserRole, ElectionType, EligibilityStatus, RiskLevel, MCCStatus, ExpenditureCategory


# ── Base ─────────────────────────────────────────────────────────────────────

class BaseResponse(BaseModel):
    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = None
    role: UserRole = UserRole.CANDIDATE

    @validator("password")
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^a-zA-Z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @validator("phone")
    def validate_phone(cls, v):
        if v and not re.match(r"^\+?[1-9]\d{9,14}$", v):
            raise ValueError("Invalid phone number format")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseResponse):
    id: UUID
    email: str
    full_name: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# CANDIDATE SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class CandidateCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    pan_number: Optional[str] = None
    aadhaar_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    address_permanent: Optional[str] = None
    address_present: Optional[str] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    education_qualification: Optional[str] = None
    occupation: Optional[str] = None
    party_affiliation: Optional[str] = None
    is_independent: bool = False
    electoral_roll_number: Optional[str] = None
    electoral_roll_state: Optional[str] = None
    electoral_roll_constituency: Optional[str] = None
    has_criminal_cases: bool = False
    has_pending_criminal_cases: bool = False
    criminal_case_details: List[Dict[str, Any]] = []
    holds_office_of_profit: bool = False
    office_of_profit_details: Optional[str] = None
    has_government_contracts: bool = False
    is_bankrupt_or_insolvent: bool = False
    notes: Optional[str] = None

    @validator("pan_number")
    def validate_pan(cls, v):
        if v and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", v.upper()):
            raise ValueError("Invalid PAN number format (e.g. ABCDE1234F)")
        return v.upper() if v else v


class CandidateUpdateRequest(CandidateCreateRequest):
    full_name: Optional[str] = None


class CandidateResponse(BaseResponse):
    id: UUID
    user_id: UUID
    full_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    pan_number: Optional[str]
    party_affiliation: Optional[str]
    is_independent: bool
    has_criminal_cases: bool
    has_pending_criminal_cases: bool
    holds_office_of_profit: bool
    is_active: bool
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# ELECTION SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class ElectionSelectionRequest(BaseModel):
    """Module 1 - Election Selection Engine input."""
    election_type: ElectionType
    state_code: str
    district_name: Optional[str] = None
    constituency_name: Optional[str] = None
    ward_name: Optional[str] = None


class ElectionSelectionResponse(BaseModel):
    election_type: ElectionType
    state: str
    applicable_provisions: List[Dict[str, Any]]
    applicable_laws: List[Dict[str, Any]]
    applicable_sec_rules: List[Dict[str, Any]]
    applicable_judgments: List[Dict[str, Any]]
    constituency_details: Optional[Dict[str, Any]] = None


class ElectionCreateRequest(BaseModel):
    constituency_id: UUID
    election_type: ElectionType
    name: str
    year: int = Field(..., ge=1950, le=2100)
    phase: Optional[int] = None
    notification_date: Optional[datetime] = None
    nomination_start_date: Optional[datetime] = None
    nomination_end_date: Optional[datetime] = None
    nomination_scrutiny_date: Optional[datetime] = None
    withdrawal_date: Optional[datetime] = None
    polling_date: Optional[datetime] = None
    counting_date: Optional[datetime] = None
    expenditure_limit: Optional[float] = None
    eci_notification_ref: Optional[str] = None


class ElectionResponse(BaseResponse):
    id: UUID
    election_type: ElectionType
    name: str
    year: int
    polling_date: Optional[datetime]
    expenditure_limit: Optional[float]
    is_active: bool
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# ELIGIBILITY SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class EligibilityCheckRequest(BaseModel):
    """Module 2 - Eligibility Assessment Engine input."""
    candidate_id: UUID
    election_type: ElectionType
    state_id: Optional[UUID] = None
    election_id: Optional[UUID] = None


class EligibilityCheckResponse(BaseResponse):
    id: UUID
    candidate_id: UUID
    election_type: ElectionType
    eligibility_status: EligibilityStatus
    eligibility_score: float
    risk_score: float
    risk_level: RiskLevel

    # Individual checks
    citizenship_check: Optional[bool]
    age_check: Optional[bool]
    age_check_details: Optional[str]
    electoral_roll_check: Optional[bool]
    office_of_profit_check: Optional[bool]
    conviction_check: Optional[bool]
    conviction_details: List[Dict]

    applicable_articles: List[Dict]
    applicable_sections: List[Dict]
    applicable_judgments: List[Dict]
    legal_explanation: Optional[str]
    recommendations: List[Dict]
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# NOMINATION READINESS SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class NominationReadinessResponse(BaseResponse):
    candidate_id: UUID
    election_id: UUID
    overall_readiness_score: float
    form_score: float
    affidavit_score: float
    security_deposit_score: float
    electoral_roll_score: float
    photograph_score: float
    pan_score: float
    assets_score: float
    liabilities_score: float
    criminal_disclosure_score: float
    pending_items: List[Dict]
    completed_items: List[Dict]


# ══════════════════════════════════════════════════════════════════════════════
# AFFIDAVIT SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class AffidavitValidationResponse(BaseResponse):
    id: UUID
    candidate_id: UUID
    election_id: UUID
    validation_status: str
    missing_fields: List[str]
    inconsistencies: List[Dict]
    potential_legal_risks: List[Dict]
    ai_analysis_notes: Optional[str]
    assets_movable: Dict
    assets_immovable: Dict
    liabilities: Dict
    criminal_cases: List[Dict]


# ══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE RISK SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class RiskAssessmentResponse(BaseResponse):
    id: UUID
    candidate_id: UUID
    eligibility_risk: Optional[RiskLevel]
    eligibility_risk_score: Optional[float]
    eligibility_risk_factors: List[Dict]
    disclosure_risk: Optional[RiskLevel]
    disclosure_risk_score: Optional[float]
    disclosure_risk_factors: List[Dict]
    legal_risk: Optional[RiskLevel]
    legal_risk_score: Optional[float]
    legal_risk_factors: List[Dict]
    expenditure_risk: Optional[RiskLevel]
    expenditure_risk_score: Optional[float]
    expenditure_risk_factors: List[Dict]
    mcc_risk: Optional[RiskLevel]
    mcc_risk_score: Optional[float]
    mcc_risk_factors: List[Dict]
    overall_risk: Optional[RiskLevel]
    overall_risk_score: Optional[float]
    executive_summary: Optional[str]
    priority_actions: List[Dict]
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# EXPENDITURE SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class ExpenditureCreateRequest(BaseModel):
    candidate_id: UUID
    election_id: UUID
    category: ExpenditureCategory
    description: str
    amount: float = Field(..., gt=0)
    expense_date: datetime
    vendor_name: Optional[str] = None
    vendor_pan: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


class ExpenditureDashboardResponse(BaseModel):
    candidate_id: UUID
    election_id: UUID
    expenditure_limit: Optional[float]
    total_spent: float
    limit_utilization_pct: Optional[float]
    risk_level: RiskLevel
    by_category: List[Dict[str, Any]]
    daily_trend: List[Dict[str, Any]]
    risk_alerts: List[str]
    recent_entries: List[Dict[str, Any]]


# ══════════════════════════════════════════════════════════════════════════════
# MCC SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class MCCCheckRequest(BaseModel):
    election_id: UUID
    candidate_id: Optional[UUID] = None
    activity_description: str = Field(..., min_length=10)
    activity_type: Optional[str] = None
    activity_date: Optional[datetime] = None
    activity_location: Optional[str] = None


class MCCCheckResponse(BaseResponse):
    id: UUID
    mcc_status: MCCStatus
    violation_category: Optional[str]
    violation_details: Optional[str]
    applicable_mcc_rules: List[Dict]
    eci_circular_refs: List[Dict]
    recommended_action: Optional[str]
    ai_confidence_score: Optional[float]
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# AI GOVERNANCE ASSISTANT SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class AIQueryRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=2000)
    context: Optional[Dict[str, Any]] = None  # candidate_id, election_type, etc.
    session_id: Optional[str] = None


class AIQueryResponse(BaseModel):
    query: str
    answer: str
    legal_basis: List[Dict[str, Any]]
    relevant_judgments: List[Dict[str, Any]]
    recommended_action: Optional[str]
    confidence_score: float
    disclaimer: str = (
        "This answer is generated by an AI system for informational purposes only. "
        "It does not constitute legal advice. Consult a qualified election law practitioner "
        "for specific legal guidance."
    )
    sources: List[Dict[str, Any]]


# ══════════════════════════════════════════════════════════════════════════════
# JUDGMENT SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class JudgmentResponse(BaseResponse):
    id: UUID
    case_name: str
    citation: Optional[str]
    year: int
    court: str
    issue: str
    ratio_decidendi: str
    impact_summary: str
    relevant_sections: List[Dict]
    affected_election_types: List[str]
    is_landmark: bool
    created_at: datetime


class JudgmentImpactResponse(BaseModel):
    """Module 11 - Judgment Impact Engine output."""
    candidate_scenario: str
    applicable_law: Dict[str, Any]
    relevant_judgment: JudgmentResponse
    compliance_requirement: str
    recommended_action: str


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class ConsultantDashboardResponse(BaseModel):
    total_candidates: int
    active_elections: int
    pending_actions_count: int
    candidates: List[Dict[str, Any]]


class CandidateSummaryCard(BaseModel):
    candidate_id: UUID
    candidate_name: str
    election_name: Optional[str]
    eligibility_status: Optional[EligibilityStatus]
    overall_risk: Optional[RiskLevel]
    readiness_score: Optional[float]
    expenditure_utilization_pct: Optional[float]
    pending_actions: List[str]
    last_updated: Optional[datetime]


# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE / LEGAL RULE SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class LegalRuleResponse(BaseResponse):
    id: UUID
    source_type: str
    section_number: Optional[str]
    title: str
    summary: Optional[str]
    applicable_election_types: List[str]
    keywords: Optional[List[str]]


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    election_type: Optional[ElectionType] = None
    source_type: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total: int
    search_time_ms: float


# ══════════════════════════════════════════════════════════════════════════════
# PAGINATION
# ══════════════════════════════════════════════════════════════════════════════

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
