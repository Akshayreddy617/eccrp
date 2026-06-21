"""
ECCRP Eligibility Service
Core business logic for Module 2 - Eligibility Assessment Engine.

Maps constitutional provisions and RP Act sections to eligibility checks.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog

from app.db.models import (
    Candidate, EligibilityCheck, EligibilityStatus, RiskLevel, ElectionType
)

logger = structlog.get_logger(__name__)


# ── Age Requirements by Election Type ────────────────────────────────────────
AGE_REQUIREMENTS = {
    ElectionType.LOK_SABHA: {"min_age": 25, "article": "Article 84(b)"},
    ElectionType.RAJYA_SABHA: {"min_age": 30, "article": "Article 84(b)"},
    ElectionType.LEGISLATIVE_ASSEMBLY: {"min_age": 25, "article": "Article 173(b)"},
    ElectionType.LEGISLATIVE_COUNCIL: {"min_age": 30, "article": "Article 173(b)"},
    ElectionType.GRAM_PANCHAYAT: {"min_age": 21, "article": "State Panchayati Raj Act"},
    ElectionType.MANDAL_PARISHAD: {"min_age": 21, "article": "State Panchayati Raj Act"},
    ElectionType.ZILLA_PARISHAD: {"min_age": 21, "article": "State Panchayati Raj Act"},
    ElectionType.MUNICIPALITY: {"min_age": 21, "article": "State Municipal Act"},
    ElectionType.MUNICIPAL_CORPORATION: {"min_age": 21, "article": "State Municipal Act"},
}

# ── Conviction Disqualification Rules (Section 8 RPA 1951) ──────────────────
CONVICTION_RULES = {
    "section_8_1": {
        "offences": [
            "promoting enmity between groups",
            "bribery in elections",
            "undue influence in elections",
            "corrupt practice under RPA",
            "offence relating to hoarding",
            "untouchability",
            "import/export violation",
            "terrorism",
            "sati",
            "cruelty to women",
            "NDPS Act offence",
            "FCRA violation",
        ],
        "disqualification_period": "6 years from conviction/release",
        "minimum_sentence_required": None,  # Any conviction
        "legal_ref": "Section 8(1) RPA 1951",
    },
    "section_8_2": {
        "offences": [
            "SEBI violation",
            "customs act",
            "foreign exchange management",
            "companies act",
        ],
        "disqualification_period": "6 years from conviction/release",
        "minimum_sentence_required": None,
        "legal_ref": "Section 8(2) RPA 1951",
    },
    "section_8_3": {
        "offences": ["any offence"],
        "disqualification_period": "6 years from release",
        "minimum_sentence_required": 2,  # 2 years imprisonment
        "legal_ref": "Section 8(3) RPA 1951",
        "key_judgment": "Lily Thomas v. Union of India (2013) 7 SCC 653",
    },
}

# ── Applicable Legal Provisions by Election Type ─────────────────────────────
ELECTION_TYPE_PROVISIONS = {
    ElectionType.LOK_SABHA: {
        "constitution_articles": [
            {"article": "84", "title": "Qualification for membership of Parliament",
             "key_points": ["citizen of India", "age ≥25 years for LS", "on electoral rolls", "no disqualification under Article 102"]},
            {"article": "102", "title": "Disqualifications for membership",
             "key_points": ["office of profit", "unsound mind", "undischarged insolvent", "non-citizen", "law disqualification"]},
        ],
        "rp_act_sections": [
            {"section": "8", "title": "Disqualification on conviction for certain offences"},
            {"section": "8A", "title": "Disqualification on ground of corrupt practices"},
            {"section": "9", "title": "Disqualification for dismissal for corruption"},
            {"section": "9A", "title": "Disqualification for government contracts"},
            {"section": "10", "title": "Disqualification for office under government"},
            {"section": "10A", "title": "Disqualification for failure to lodge account"},
            {"section": "11A", "title": "Disqualification on ground of election offence"},
        ],
    },
    ElectionType.LEGISLATIVE_ASSEMBLY: {
        "constitution_articles": [
            {"article": "173", "title": "Qualification for membership of State Legislature",
             "key_points": ["citizen", "age ≥25 for LA", "voter in state constituency"]},
            {"article": "191", "title": "Disqualifications for membership of State Legislature"},
        ],
        "rp_act_sections": [
            {"section": "8", "title": "Disqualification on conviction"},
            {"section": "9A", "title": "Government contracts"},
            {"section": "10A", "title": "Failure to lodge expenditure account"},
        ],
    },
}
# Reuse LA provisions for LC
ELECTION_TYPE_PROVISIONS[ElectionType.LEGISLATIVE_COUNCIL] = ELECTION_TYPE_PROVISIONS[ElectionType.LEGISLATIVE_ASSEMBLY]
# Rajya Sabha uses Parliament provisions
ELECTION_TYPE_PROVISIONS[ElectionType.RAJYA_SABHA] = ELECTION_TYPE_PROVISIONS[ElectionType.LOK_SABHA]

LOCAL_BODY_PROVISIONS = {
    "constitution_articles": [
        {"article": "243F", "title": "Disqualifications for membership of Panchayats"},
        {"article": "243V", "title": "Disqualifications for membership of Municipalities"},
    ],
    "rp_act_sections": [],
}
for et in [ElectionType.GRAM_PANCHAYAT, ElectionType.MANDAL_PARISHAD,
           ElectionType.ZILLA_PARISHAD, ElectionType.MUNICIPALITY, ElectionType.MUNICIPAL_CORPORATION]:
    ELECTION_TYPE_PROVISIONS[et] = LOCAL_BODY_PROVISIONS

# ── Key Judgments ─────────────────────────────────────────────────────────────
KEY_JUDGMENTS = [
    {
        "case": "Lily Thomas v. Union of India",
        "citation": "(2013) 7 SCC 653",
        "issue": "Instant disqualification on conviction with ≥2 years imprisonment",
        "impact": "Cannot contest elections if convicted for ≥2 years even if appeal pending",
        "relevant_section": "Section 8(3) RPA 1951",
    },
    {
        "case": "Association for Democratic Reforms v. Union of India",
        "citation": "(2002) 5 SCC 294",
        "issue": "Mandatory disclosure of criminal antecedents, assets, and liabilities",
        "impact": "Voters have fundamental right to know candidate background",
        "relevant_section": "Section 33A RPA 1951",
    },
    {
        "case": "Public Interest Foundation v. Union of India",
        "citation": "(2019) 3 SCC 224",
        "issue": "Political parties must publicise reasons for fielding candidates with criminal cases",
        "impact": "Enhanced disclosure obligation on parties",
        "relevant_section": "Section 8 RPA 1951",
    },
]


class EligibilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_full_check(
        self,
        candidate_id: UUID,
        election_type: ElectionType,
        state_id: Optional[UUID],
        election_id: Optional[UUID],
        checked_by_user_id: UUID,
    ) -> EligibilityCheck:
        # Load candidate
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        candidate: Candidate = result.scalar_one_or_none()
        if not candidate:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Mark previous checks as not latest
        await self.db.execute(
            update(EligibilityCheck)
            .where(
                EligibilityCheck.candidate_id == candidate_id,
                EligibilityCheck.is_latest == True,
            )
            .values(is_latest=False)
        )

        # Run individual checks
        checks = {}
        checks["citizenship"] = self._check_citizenship(candidate)
        checks["age"] = self._check_age(candidate, election_type)
        checks["electoral_roll"] = self._check_electoral_roll(candidate)
        checks["office_of_profit"] = self._check_office_of_profit(candidate)
        checks["corrupt_practices"] = True  # Requires separate court record lookup
        checks["government_contract"] = not candidate.has_government_contracts
        checks["insolvency"] = not candidate.is_bankrupt_or_insolvent
        checks["conviction"] = self._check_convictions(candidate)
        checks["election_expenditure"] = True  # Requires ECI data lookup
        checks["reservation"] = True  # Depends on constituency data
        checks["local_body"] = self._check_local_body(candidate, election_type)

        # Calculate scores
        eligibility_status, eligibility_score, risk_score, risk_level = (
            self._calculate_scores(checks, candidate, election_type)
        )

        # Get applicable provisions
        provisions = ELECTION_TYPE_PROVISIONS.get(election_type, {})
        applicable_articles = provisions.get("constitution_articles", [])
        applicable_sections = provisions.get("rp_act_sections", [])

        # Build legal explanation
        legal_explanation = self._build_legal_explanation(
            checks, candidate, election_type, eligibility_status
        )

        # Build recommendations
        recommendations = self._build_recommendations(checks, candidate, election_type)

        # Determine conviction details
        conviction_details = []
        if candidate.criminal_case_details:
            for case in candidate.criminal_case_details:
                if case.get("convicted") and case.get("sentence_years", 0) >= 2:
                    conviction_details.append({
                        "case_number": case.get("case_number"),
                        "offence": case.get("offence"),
                        "sentence_years": case.get("sentence_years"),
                        "disqualification": "Section 8(3) RPA 1951 — 6 years from release",
                        "judgment_ref": "Lily Thomas v. Union of India (2013)",
                    })

        check = EligibilityCheck(
            candidate_id=candidate_id,
            election_id=election_id,
            election_type=election_type,
            state_id=state_id,
            citizenship_check=checks["citizenship"],
            age_check=checks["age"]["passed"],
            age_check_details=checks["age"]["details"],
            electoral_roll_check=checks["electoral_roll"],
            office_of_profit_check=checks["office_of_profit"],
            corrupt_practices_check=checks["corrupt_practices"],
            government_contract_check=checks["government_contract"],
            insolvency_check=checks["insolvency"],
            conviction_check=checks["conviction"]["passed"],
            conviction_details=conviction_details,
            election_expenditure_violation_check=checks["election_expenditure"],
            reservation_eligibility_check=checks["reservation"],
            local_body_eligibility_check=checks["local_body"],
            eligibility_status=eligibility_status,
            eligibility_score=eligibility_score,
            risk_score=risk_score,
            risk_level=risk_level,
            applicable_articles=applicable_articles,
            applicable_sections=applicable_sections,
            applicable_judgments=KEY_JUDGMENTS,
            legal_explanation=legal_explanation,
            recommendations=recommendations,
            checked_by_user_id=checked_by_user_id,
            is_latest=True,
        )

        self.db.add(check)
        await self.db.flush()
        await self.db.refresh(check)
        logger.info(
            "eligibility_check_completed",
            candidate_id=str(candidate_id),
            status=eligibility_status.value,
            risk=risk_level.value,
        )
        return check

    def _check_citizenship(self, candidate: Candidate) -> bool:
        """Article 84(a) / 173(a): Must be a citizen of India."""
        # In real system: verify against citizenship documents
        return True  # Default: assume citizen unless flagged

    def _check_age(self, candidate: Candidate, election_type: ElectionType) -> dict:
        req = AGE_REQUIREMENTS.get(election_type, {"min_age": 25, "article": "Applicable Act"})
        if not candidate.date_of_birth:
            return {
                "passed": False,
                "details": "Date of birth not provided. Cannot verify age eligibility.",
            }
        today = datetime.now(timezone.utc)
        dob = candidate.date_of_birth.replace(tzinfo=timezone.utc) if candidate.date_of_birth.tzinfo is None else candidate.date_of_birth
        age = (today - dob).days // 365
        passed = age >= req["min_age"]
        return {
            "passed": passed,
            "details": (
                f"Age: {age} years. Required: ≥{req['min_age']} years per {req['article']}. "
                f"{'PASS' if passed else 'FAIL — does not meet minimum age requirement.'}"
            ),
        }

    def _check_electoral_roll(self, candidate: Candidate) -> bool:
        """Must be enrolled as a voter. Article 84(c)/173(c)."""
        return bool(candidate.electoral_roll_number and candidate.electoral_roll_state)

    def _check_office_of_profit(self, candidate: Candidate) -> bool:
        """Article 102(1)(a)/191(1)(a): No office of profit under Government."""
        return not candidate.holds_office_of_profit

    def _check_convictions(self, candidate: Candidate) -> dict:
        """Section 8 RPA 1951: Check disqualifying convictions."""
        if not candidate.has_criminal_cases:
            return {"passed": True, "details": "No criminal cases declared."}

        disqualifying = []
        for case in (candidate.criminal_case_details or []):
            if case.get("convicted"):
                sentence_years = case.get("sentence_years", 0)
                if sentence_years >= 2:
                    disqualifying.append(case)

        if disqualifying:
            return {
                "passed": False,
                "details": f"{len(disqualifying)} disqualifying conviction(s) found under Section 8(3) RPA 1951.",
                "disqualifying_cases": disqualifying,
            }
        if candidate.has_pending_criminal_cases:
            return {
                "passed": True,
                "details": "Pending criminal cases — must be disclosed in Form 26 as per ADR judgment. Not a bar to contesting unless convicted.",
                "warning": True,
            }
        return {"passed": True, "details": "No disqualifying convictions found."}

    def _check_local_body(self, candidate: Candidate, election_type: ElectionType) -> bool:
        """State-specific local body eligibility (tax dues, domicile, etc.)."""
        local_body_types = {
            ElectionType.GRAM_PANCHAYAT, ElectionType.MANDAL_PARISHAD,
            ElectionType.ZILLA_PARISHAD, ElectionType.MUNICIPALITY,
            ElectionType.MUNICIPAL_CORPORATION,
        }
        if election_type not in local_body_types:
            return True
        # State-specific checks would query state rules here
        return True

    def _calculate_scores(
        self, checks: dict, candidate: Candidate, election_type: ElectionType
    ) -> tuple:
        # Critical failures = immediate disqualification
        critical_checks = {
            "citizenship": checks["citizenship"],
            "insolvency": checks["insolvency"],
            "conviction": checks["conviction"]["passed"],
            "office_of_profit": checks["office_of_profit"],
        }

        if not all(critical_checks.values()):
            return EligibilityStatus.DISQUALIFIED, 0.0, 100.0, RiskLevel.CRITICAL

        # Score calculation
        weighted_checks = {
            "citizenship": (checks["citizenship"], 25),
            "age": (checks["age"]["passed"], 20),
            "electoral_roll": (checks["electoral_roll"], 15),
            "office_of_profit": (checks["office_of_profit"], 10),
            "government_contract": (checks["government_contract"], 10),
            "insolvency": (checks["insolvency"], 10),
            "conviction": (checks["conviction"]["passed"], 10),
        }

        total_weight = sum(w for _, (_, w) in weighted_checks.items())
        earned = sum(w for _, (passed, w) in weighted_checks.items() if passed)
        eligibility_score = (earned / total_weight) * 100
        risk_score = 100 - eligibility_score

        # Pending criminal cases add risk
        if candidate.has_pending_criminal_cases:
            risk_score = min(100, risk_score + 20)

        if eligibility_score >= 90:
            status = EligibilityStatus.ELIGIBLE
            risk_level = RiskLevel.LOW
        elif eligibility_score >= 70:
            status = EligibilityStatus.POTENTIALLY_ELIGIBLE
            risk_level = RiskLevel.MEDIUM
        elif eligibility_score >= 50:
            status = EligibilityStatus.HIGH_RISK
            risk_level = RiskLevel.HIGH
        else:
            status = EligibilityStatus.DISQUALIFIED
            risk_level = RiskLevel.CRITICAL

        return status, round(eligibility_score, 2), round(risk_score, 2), risk_level

    def _build_legal_explanation(
        self, checks: dict, candidate: Candidate,
        election_type: ElectionType, status: EligibilityStatus
    ) -> str:
        lines = [
            f"Eligibility Assessment for {election_type.value.replace('_', ' ').title()}",
            "=" * 60,
        ]

        if status == EligibilityStatus.ELIGIBLE:
            lines.append("✅ The candidate appears ELIGIBLE to contest this election.")
        elif status == EligibilityStatus.POTENTIALLY_ELIGIBLE:
            lines.append("⚠️ The candidate is POTENTIALLY ELIGIBLE but has risk factors requiring attention.")
        elif status == EligibilityStatus.HIGH_RISK:
            lines.append("🔴 The candidate is HIGH RISK. Legal consultation strongly recommended.")
        else:
            lines.append("❌ The candidate appears DISQUALIFIED from contesting this election.")

        lines.append("")
        lines.append("CHECK-WISE ANALYSIS:")

        check_map = [
            ("Citizenship", checks["citizenship"], "Article 84(a)/173(a) Constitution of India"),
            ("Age Requirement", checks["age"]["passed"], checks["age"]["details"]),
            ("Electoral Roll", checks["electoral_roll"], "Article 84(c)/173(c) & Section 19 RPA 1950"),
            ("Office of Profit", checks["office_of_profit"], "Article 102(1)(a)/191(1)(a) Constitution"),
            ("Government Contracts", checks["government_contract"], "Section 9A RPA 1951"),
            ("Insolvency", checks["insolvency"], "Section 9 RPA 1951"),
            ("Convictions", checks["conviction"]["passed"], checks["conviction"]["details"]),
        ]

        for name, passed, detail in check_map:
            symbol = "✅" if passed else "❌"
            lines.append(f"\n{symbol} {name}")
            lines.append(f"   Legal Basis: {detail}")

        if candidate.has_pending_criminal_cases:
            lines.append(
                "\n⚠️ PENDING CRIMINAL CASES: While pending cases do not bar candidacy, "
                "they MUST be disclosed in Form 26 (Affidavit). "
                "Failure to disclose is a ground for election petition. "
                "Ref: ADR v. Union of India (2002), Public Interest Foundation (2019)."
            )

        return "\n".join(lines)

    def _build_recommendations(
        self, checks: dict, candidate: Candidate, election_type: ElectionType
    ) -> list:
        recs = []

        if not checks["electoral_roll"]:
            recs.append({
                "priority": "CRITICAL",
                "action": "Register on electoral roll immediately",
                "legal_basis": "Article 84(c) Constitution / Section 19 RPA 1950",
                "timeline": "Before nomination filing",
            })

        if not checks["age"]["passed"]:
            recs.append({
                "priority": "CRITICAL",
                "action": "Candidate does not meet minimum age requirement",
                "legal_basis": AGE_REQUIREMENTS.get(election_type, {}).get("article", ""),
                "timeline": "Cannot contest until age requirement is met",
            })

        if not checks["office_of_profit"]:
            recs.append({
                "priority": "CRITICAL",
                "action": "Resign from office of profit before filing nomination",
                "legal_basis": "Article 102(1)(a) / Section 9 RPA 1951",
                "timeline": "Must be done before nomination",
            })

        if not checks["government_contract"]:
            recs.append({
                "priority": "HIGH",
                "action": "Resolve or transfer all government contracts",
                "legal_basis": "Section 9A RPA 1951",
                "timeline": "Before nomination filing",
            })

        if candidate.has_pending_criminal_cases:
            recs.append({
                "priority": "HIGH",
                "action": "Ensure all pending criminal cases are fully disclosed in Form 26",
                "legal_basis": "Section 33A RPA 1951; ADR v. Union of India (2002)",
                "timeline": "At time of nomination filing",
            })

        if not recs:
            recs.append({
                "priority": "LOW",
                "action": "Proceed with nomination filing. Ensure all documents are complete.",
                "legal_basis": "Section 33 RPA 1951",
                "timeline": "Within nomination window",
            })

        return recs
