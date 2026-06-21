"""
ECCRP Database Models
Complete ORM definitions for all platform entities.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Date
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint, Index, Numeric,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


# ══════════════════════════════════════════════════════════════════════════════
# ENUMERATIONS
# ══════════════════════════════════════════════════════════════════════════════

class ElectionType(str, enum.Enum):
    LOK_SABHA = "lok_sabha"
    RAJYA_SABHA = "rajya_sabha"
    LEGISLATIVE_ASSEMBLY = "legislative_assembly"
    LEGISLATIVE_COUNCIL = "legislative_council"
    GRAM_PANCHAYAT = "gram_panchayat"
    MANDAL_PARISHAD = "mandal_parishad"
    ZILLA_PARISHAD = "zilla_parishad"
    MUNICIPALITY = "municipality"
    MUNICIPAL_CORPORATION = "municipal_corporation"


class EligibilityStatus(str, enum.Enum):
    ELIGIBLE = "eligible"
    POTENTIALLY_ELIGIBLE = "potentially_eligible"
    HIGH_RISK = "high_risk"
    DISQUALIFIED = "disqualified"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MCCStatus(str, enum.Enum):
    COMPLIANT = "compliant"
    POTENTIAL_VIOLATION = "potential_violation"
    VIOLATION = "violation"


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    CONSULTANT = "consultant"
    CANDIDATE = "candidate"
    LAWYER = "lawyer"
    JOURNALIST = "journalist"
    RESEARCHER = "researcher"
    PUBLIC = "public"


class DocumentType(str, enum.Enum):
    FORM_26 = "form_26"
    ASSETS_DECLARATION = "assets_declaration"
    LIABILITIES_DECLARATION = "liabilities_declaration"
    CRIMINAL_DISCLOSURE = "criminal_disclosure"
    ELECTORAL_ROLL_PROOF = "electoral_roll_proof"
    IDENTITY_PROOF = "identity_proof"
    OTHER = "other"


class KnowledgeArticleType(str, enum.Enum):
    CONSTITUTION_ARTICLE = "constitution_article"
    RP_ACT_1950 = "rp_act_1950"
    RP_ACT_1951 = "rp_act_1951"
    CONDUCT_OF_ELECTION_RULES = "conduct_of_election_rules"
    ECI_CIRCULAR = "eci_circular"
    SEC_CIRCULAR = "sec_circular"
    PCI_GUIDELINE = "pci_guideline"
    RNI_RULE = "rni_rule"
    MCC_GUIDELINE = "mcc_guideline"


class ExpenditureCategory(str, enum.Enum):
    VEHICLE = "vehicle"
    ADVERTISING_PRINT = "advertising_print"
    ADVERTISING_DIGITAL = "advertising_digital"
    ADVERTISING_OUTDOOR = "advertising_outdoor"
    MEETINGS_RALLIES = "meetings_rallies"
    TRAVEL = "travel"
    VOLUNTEERS = "volunteers"
    CAMPAIGN_MATERIALS = "campaign_materials"
    SOUND_EQUIPMENT = "sound_equipment"
    OTHER = "other"


# ══════════════════════════════════════════════════════════════════════════════
# MIXINS
# ══════════════════════════════════════════════════════════════════════════════

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)


# ══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHIC / ADMINISTRATIVE ENTITIES
# ══════════════════════════════════════════════════════════════════════════════

class State(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "states"

    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)  # e.g., AP, TN, MH
    is_union_territory = Column(Boolean, default=False)
    has_legislative_council = Column(Boolean, default=False)
    sec_name = Column(String(200))  # State Election Commission name
    ec_contact = Column(JSONB)  # Contact details
    is_active = Column(Boolean, default=True)

    districts = relationship("District", back_populates="state")
    constituencies = relationship("Constituency", back_populates="state")


class District(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "districts"

    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(20))
    headquarters = Column(String(100))
    is_active = Column(Boolean, default=True)

    state = relationship("State", back_populates="districts")
    constituencies = relationship("Constituency", back_populates="district")

    __table_args__ = (
        UniqueConstraint("state_id", "name", name="uq_district_state_name"),
        Index("ix_districts_state_id", "state_id"),
    )


class Constituency(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "constituencies"

    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=False)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"))
    election_type = Column(Enum(ElectionType), nullable=False)
    name = Column(String(200), nullable=False)
    number = Column(Integer)  # Constituency number as per ECI
    reservation_category = Column(String(50))  # GEN, SC, ST, OBC, WOMEN
    total_voters = Column(BigInteger)
    is_active = Column(Boolean, default=True)

    state = relationship("State", back_populates="constituencies")
    district = relationship("District", back_populates="constituencies")
    elections = relationship("Election", back_populates="constituency")

    __table_args__ = (
        Index("ix_constituency_state_type", "state_id", "election_type"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# USER & AUTH
# ══════════════════════════════════════════════════════════════════════════════

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CANDIDATE)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    profile_data = Column(JSONB, default={})  # Additional profile fields
    preferences = Column(JSONB, default={})

    candidates = relationship("Candidate", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    device_info = Column(JSONB)

    user = relationship("User")
    __table_args__ = (Index("ix_refresh_tokens_user_id", "user_id"),)


# ══════════════════════════════════════════════════════════════════════════════
# CANDIDATE & ELECTION
# ══════════════════════════════════════════════════════════════════════════════

class Candidate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "candidates"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    full_name = Column(String(200), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(20))
    pan_number = Column(String(20))
    aadhaar_last4 = Column(String(4))  # Only last 4 for privacy
    address_permanent = Column(Text)
    address_present = Column(Text)
    phone_primary = Column(String(20))
    phone_secondary = Column(String(20))
    email = Column(String(255))
    education_qualification = Column(String(200))
    occupation = Column(String(200))
    party_affiliation = Column(String(200))
    is_independent = Column(Boolean, default=False)
    electoral_roll_number = Column(String(100))
    electoral_roll_state = Column(String(100))
    electoral_roll_constituency = Column(String(200))
    has_criminal_cases = Column(Boolean, default=False)
    has_pending_criminal_cases = Column(Boolean, default=False)
    criminal_case_details = Column(JSONB, default=[])
    holds_office_of_profit = Column(Boolean, default=False)
    office_of_profit_details = Column(Text)
    has_government_contracts = Column(Boolean, default=False)
    is_bankrupt_or_insolvent = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    user = relationship("User", back_populates="candidates")
    election_participations = relationship("ElectionParticipation", back_populates="candidate")
    eligibility_checks = relationship("EligibilityCheck", back_populates="candidate")
    nomination_documents = relationship("NominationDocument", back_populates="candidate")
    affidavits = relationship("Affidavit", back_populates="candidate")
    expenditures = relationship("Expenditure", back_populates="candidate")
    risk_assessments = relationship("RiskAssessment", back_populates="candidate")

    __table_args__ = (Index("ix_candidates_user_id", "user_id"),)


class Election(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "elections"

    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"), nullable=False)
    election_type = Column(Enum(ElectionType), nullable=False)
    name = Column(String(300), nullable=False)
    year = Column(Integer, nullable=False)
    phase = Column(Integer)  # Phase number for multi-phase elections
    notification_date = Column(DateTime(timezone=True))
    nomination_start_date = Column(DateTime(timezone=True))
    nomination_end_date = Column(DateTime(timezone=True))
    nomination_scrutiny_date = Column(DateTime(timezone=True))
    withdrawal_date = Column(DateTime(timezone=True))
    polling_date = Column(DateTime(timezone=True))
    counting_date = Column(DateTime(timezone=True))
    result_date = Column(DateTime(timezone=True))
    expenditure_limit = Column(Numeric(15, 2))  # In INR
    mcc_start_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    eci_notification_ref = Column(String(200))
    notes = Column(Text)

    constituency = relationship("Constituency", back_populates="elections")
    participations = relationship("ElectionParticipation", back_populates="election")
    mcc_checks = relationship("MCCCheck", back_populates="election")

    __table_args__ = (
        Index("ix_elections_constituency_year", "constituency_id", "year"),
        Index("ix_elections_type_year", "election_type", "year"),
    )


class ElectionParticipation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "election_participations"

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id"), nullable=False)
    party_symbol = Column(String(100))
    nomination_filed = Column(Boolean, default=False)
    nomination_accepted = Column(Boolean)
    withdrew = Column(Boolean, default=False)
    final_status = Column(String(50))  # won, lost, withdrew, rejected
    votes_polled = Column(BigInteger)
    rank = Column(Integer)
    security_deposit_amount = Column(Numeric(10, 2))
    security_deposit_forfeited = Column(Boolean)

    candidate = relationship("Candidate", back_populates="election_participations")
    election = relationship("Election", back_populates="participations")

    __table_args__ = (
        UniqueConstraint("candidate_id", "election_id", name="uq_participation"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE MODULES
# ══════════════════════════════════════════════════════════════════════════════

class EligibilityCheck(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "eligibility_checks"

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id"))
    election_type = Column(Enum(ElectionType), nullable=False)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"))

    # Check results
    citizenship_check = Column(Boolean)
    age_check = Column(Boolean)
    age_check_details = Column(Text)
    electoral_roll_check = Column(Boolean)
    electoral_roll_details = Column(Text)
    office_of_profit_check = Column(Boolean)
    corrupt_practices_check = Column(Boolean)
    government_contract_check = Column(Boolean)
    insolvency_check = Column(Boolean)
    conviction_check = Column(Boolean)
    conviction_details = Column(JSONB, default=[])
    election_expenditure_violation_check = Column(Boolean)
    reservation_eligibility_check = Column(Boolean)
    reservation_eligibility_details = Column(Text)
    local_body_eligibility_check = Column(Boolean)

    # Scores
    eligibility_status = Column(Enum(EligibilityStatus))
    eligibility_score = Column(Float)  # 0–100
    risk_score = Column(Float)  # 0–100
    risk_level = Column(Enum(RiskLevel))

    # Legal basis
    applicable_articles = Column(JSONB, default=[])  # Constitution articles
    applicable_sections = Column(JSONB, default=[])  # RP Act sections
    applicable_judgments = Column(JSONB, default=[])  # SC judgment references
    legal_explanation = Column(Text)
    recommendations = Column(JSONB, default=[])

    checked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_latest = Column(Boolean, default=True)

    candidate = relationship("Candidate", back_populates="eligibility_checks")

    __table_args__ = (
        Index("ix_eligibility_checks_candidate", "candidate_id"),
        Index("ix_eligibility_checks_latest", "candidate_id", "is_latest"),
    )


class NominationDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "nomination_documents"

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    document_name = Column(String(300))
    minio_object_key = Column(String(500))  # Object storage reference
    file_size_bytes = Column(BigInteger)
    mime_type = Column(String(100))
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Computed readiness fields
    is_complete = Column(Boolean, default=False)
    missing_fields = Column(JSONB, default=[])
    validation_errors = Column(JSONB, default=[])

    candidate = relationship("Candidate", back_populates="nomination_documents")

    __table_args__ = (
        Index("ix_nomination_docs_candidate_election", "candidate_id", "election_id"),
    )


class NominationReadiness(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "nomination_readiness"

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, unique=True)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id"), nullable=False)

    # Component scores
    form_score = Column(Float, default=0.0)
    affidavit_score = Column(Float, default=0.0)
    security_deposit_score = Column(Float, default=0.0)
    electoral_roll_score = Column(Float, default=0.0)
    photograph_score = Column(Float, default=0.0)
    pan_score = Column(Float, default=0.0)
    assets_score = Column(Float, default=0.0)
    liabilities_score = Column(Float, default=0.0)
    criminal_disclosure_score = Column(Float, default=0.0)

    overall_readiness_score = Column(Float, default=0.0)
    pending_items = Column(JSONB, default=[])
    completed_items = Column(JSONB, default=[])

    candidate = relationship("Candidate")


class Affidavit(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "affidavits"

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id"), nullable=False)
    form_number = Column(String(20), default="Form 26")
    minio_object_key = Column(String(500))

    # Parsed content (from AI extraction)
    assets_movable = Column(JSONB, default={})
    assets_immovable = Column(JSONB, default={})
    liabilities = Column(JSONB, default={})
    criminal_cases = Column(JSONB, default=[])
    pan_number = Column(String(20))
    educational_qualification = Column(String(200))

    # Validation results
    validation_status = Column(String(50))  # complete, incomplete, inconsistent
    missing_fields = Column(JSONB, default=[])
    inconsistencies = Column(JSONB, default=[])
    potential_legal_risks = Column(JSONB, default=[])
    ai_analysis_notes = Column(Text)

    is_original = Column(Boolean, default=True)
    submission_date = Column(DateTime(timezone=True))

    candidate = relationship("Candidate", back_populates="affidavits")

    __table_args__ = (
        Index("ix_affidavits_candidate_election", "candidate_id", "election_id"),
    )


class Expenditure(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "expenditures"

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id"), nullable=False)
    category = Column(Enum(ExpenditureCategory), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    expense_date = Column(DateTime(timezone=True), nullable=False)
    vendor_name = Column(String(300))
    vendor_pan = Column(String(20))
    receipt_number = Column(String(100))
    minio_receipt_key = Column(String(500))  # Receipt image/PDF
    is_disputed = Column(Boolean, default=False)
    notes = Column(Text)

    candidate = relationship("Candidate", back_populates="expenditures")

    __table_args__ = (
        Index("ix_expenditures_candidate_election", "candidate_id", "election_id"),
        Index("ix_expenditures_date", "expense_date"),
    )


class MCCCheck(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "mcc_checks"

    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"))
    checked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    activity_description = Column(Text, nullable=False)
    activity_type = Column(String(100))  # rally, advertisement, social_media, gift_distribution, etc.
    activity_date = Column(DateTime(timezone=True))
    activity_location = Column(String(500))

    mcc_status = Column(Enum(MCCStatus), nullable=False)
    violation_category = Column(String(200))
    violation_details = Column(Text)
    applicable_mcc_rules = Column(JSONB, default=[])
    eci_circular_refs = Column(JSONB, default=[])
    state_rules_refs = Column(JSONB, default=[])
    recommended_action = Column(Text)
    ai_confidence_score = Column(Float)  # 0–1

    election = relationship("Election", back_populates="mcc_checks")

    __table_args__ = (Index("ix_mcc_checks_election", "election_id"),)


class RiskAssessment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "risk_assessments"

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id"))

    eligibility_risk = Column(Enum(RiskLevel))
    eligibility_risk_score = Column(Float)
    eligibility_risk_factors = Column(JSONB, default=[])

    disclosure_risk = Column(Enum(RiskLevel))
    disclosure_risk_score = Column(Float)
    disclosure_risk_factors = Column(JSONB, default=[])

    legal_risk = Column(Enum(RiskLevel))
    legal_risk_score = Column(Float)
    legal_risk_factors = Column(JSONB, default=[])

    expenditure_risk = Column(Enum(RiskLevel))
    expenditure_risk_score = Column(Float)
    expenditure_risk_factors = Column(JSONB, default=[])

    mcc_risk = Column(Enum(RiskLevel))
    mcc_risk_score = Column(Float)
    mcc_risk_factors = Column(JSONB, default=[])

    overall_risk = Column(Enum(RiskLevel))
    overall_risk_score = Column(Float)
    executive_summary = Column(Text)
    priority_actions = Column(JSONB, default=[])

    is_latest = Column(Boolean, default=True)

    candidate = relationship("Candidate", back_populates="risk_assessments")

    __table_args__ = (
        Index("ix_risk_assessments_candidate_latest", "candidate_id", "is_latest"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# LEGAL KNOWLEDGE REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class LegalRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "legal_rules"

    source_type = Column(Enum(KnowledgeArticleType), nullable=False)
    section_number = Column(String(50))  # e.g., "Article 84", "Section 8", "Rule 4"
    title = Column(String(500), nullable=False)
    full_text = Column(Text, nullable=False)
    summary = Column(Text)
    applicable_election_types = Column(JSONB, default=[])
    keywords = Column(ARRAY(String))
    embedding_vector_id = Column(String(200))  # OpenSearch doc ID
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime(timezone=True))
    effective_until = Column(DateTime(timezone=True))
    superseded_by_id = Column(UUID(as_uuid=True), ForeignKey("legal_rules.id"))
    amendment_notes = Column(Text)

    judgment_mappings = relationship("JudgmentMapping", back_populates="rule")

    __table_args__ = (
        Index("ix_legal_rules_source_section", "source_type", "section_number"),
    )


class Judgment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "judgments"

    case_name = Column(String(500), nullable=False)
    citation = Column(String(200))  # e.g., "(2002) 3 SCC 294"
    year = Column(Integer, nullable=False)
    court = Column(String(200), nullable=False)  # Supreme Court, High Court, etc.
    bench_composition = Column(String(300))
    issue = Column(Text, nullable=False)
    ratio_decidendi = Column(Text, nullable=False)  # Core legal holding
    obiter_dicta = Column(Text)
    impact_summary = Column(Text, nullable=False)
    relevant_sections = Column(JSONB, default=[])  # RP Act, Constitution sections
    affected_election_types = Column(JSONB, default=[])
    keywords = Column(ARRAY(String))
    full_text_url = Column(String(500))
    embedding_vector_id = Column(String(200))
    is_landmark = Column(Boolean, default=False)
    overruled_by_id = Column(UUID(as_uuid=True), ForeignKey("judgments.id"))

    __table_args__ = (
        Index("ix_judgments_year", "year"),
        Index("ix_judgments_landmark", "is_landmark"),
    )


class JudgmentMapping(Base, UUIDMixin, TimestampMixin):
    """Maps judgments to legal rules and compliance requirements."""
    __tablename__ = "judgment_mappings"

    judgment_id = Column(UUID(as_uuid=True), ForeignKey("judgments.id"), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("legal_rules.id"), nullable=False)
    mapping_type = Column(String(100))  # interprets, expands, restricts, overrules
    compliance_requirement = Column(Text, nullable=False)
    triggered_by = Column(String(200))  # What candidate action triggers this
    notes = Column(Text)

    judgment = relationship("Judgment")
    rule = relationship("LegalRule", back_populates="judgment_mappings")

    __table_args__ = (
        UniqueConstraint("judgment_id", "rule_id", name="uq_judgment_rule"),
    )


class KnowledgeArticle(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_articles"

    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False)
    article_type = Column(Enum(KnowledgeArticleType), nullable=False)
    summary = Column(Text)
    content = Column(Text, nullable=False)  # Markdown
    applicable_election_types = Column(JSONB, default=[])
    tags = Column(ARRAY(String))
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True))
    author = Column(String(200))
    view_count = Column(Integer, default=0)
    embedding_vector_id = Column(String(200))

    __table_args__ = (Index("ix_knowledge_articles_type", "article_type"),)


# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH NODES & EDGES (Neo4j mirrored in PG for audit)
# ══════════════════════════════════════════════════════════════════════════════

class KnowledgeGraphNode(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_graph_nodes"

    neo4j_node_id = Column(String(100), unique=True)
    node_type = Column(String(100), nullable=False)  # Article, Section, Rule, Judgment, Requirement
    label = Column(String(500), nullable=False)
    properties = Column(JSONB, default={})
    source_entity_type = Column(String(100))  # legal_rule, judgment, etc.
    source_entity_id = Column(UUID(as_uuid=True))

    __table_args__ = (Index("ix_kg_nodes_type", "node_type"),)


class KnowledgeGraphEdge(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_graph_edges"

    neo4j_edge_id = Column(String(100), unique=True)
    from_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id"), nullable=False)
    to_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)  # INTERPRETS, REQUIRES, SUPERSEDES, etc.
    weight = Column(Float, default=1.0)
    properties = Column(JSONB, default={})

    __table_args__ = (
        Index("ix_kg_edges_from", "from_node_id"),
        Index("ix_kg_edges_to", "to_node_id"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# AI QUERY LOG
# ══════════════════════════════════════════════════════════════════════════════

class AIQueryLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_query_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    query = Column(Text, nullable=False)
    response = Column(Text)
    legal_basis = Column(JSONB, default=[])  # Citations used
    confidence_score = Column(Float)
    relevant_judgments = Column(JSONB, default=[])
    model_used = Column(String(100))
    tokens_used = Column(Integer)
    latency_ms = Column(Integer)
    was_helpful = Column(Boolean)  # User feedback
    session_id = Column(String(100))

    __table_args__ = (Index("ix_ai_query_logs_user", "user_id"),)


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS & AUDIT
# ══════════════════════════════════════════════════════════════════════════════

class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(100))  # deadline, risk_alert, compliance, system
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    action_url = Column(String(500))
    notification_metadata = Column(JSONB, default={})

    user = relationship("User", back_populates="notifications")
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(200), nullable=False)  # e.g., ELIGIBILITY_CHECK_CREATED
    resource_type = Column(String(100))  # candidate, election, affidavit, etc.
    resource_id = Column(UUID(as_uuid=True))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(String(100))
    before_state = Column(JSONB)
    after_state = Column(JSONB)
    status = Column(String(20))  # success, failure
    error_message = Column(Text)

    user = relationship("User", back_populates="audit_logs")
    __table_args__ = (
        Index("ix_audit_logs_user", "user_id"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_created", "created_at"),
    )
