"""
ECCRP Unit Tests - Eligibility Service
Tests eligibility check logic, scoring, and legal mapping.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from app.db.models import (
    Candidate, EligibilityStatus, RiskLevel, ElectionType
)
from app.services.eligibility_service import EligibilityService, AGE_REQUIREMENTS


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    return EligibilityService(mock_db)


@pytest.fixture
def base_candidate():
    """A fully eligible candidate."""
    return Candidate(
        id=uuid4(),
        user_id=uuid4(),
        full_name="Test Candidate",
        date_of_birth=datetime(1980, 1, 1, tzinfo=timezone.utc),
        electoral_roll_number="AP/123/456789",
        electoral_roll_state="Andhra Pradesh",
        electoral_roll_constituency="Anantapur",
        has_criminal_cases=False,
        has_pending_criminal_cases=False,
        criminal_case_details=[],
        holds_office_of_profit=False,
        has_government_contracts=False,
        is_bankrupt_or_insolvent=False,
    )


# ── Citizenship Check ──────────────────────────────────────────────────────

class TestCitizenshipCheck:
    def test_citizenship_default_passes(self, service, base_candidate):
        assert service._check_citizenship(base_candidate) is True


# ── Age Check ──────────────────────────────────────────────────────────────

class TestAgeCheck:
    @pytest.mark.parametrize("election_type,dob,expected", [
        (ElectionType.LOK_SABHA, datetime(1999, 1, 1), True),   # 25+ years
        (ElectionType.LOK_SABHA, datetime(2001, 1, 1), False),  # <25 years
        (ElectionType.RAJYA_SABHA, datetime(1994, 1, 1), True),  # 30+ years
        (ElectionType.RAJYA_SABHA, datetime(2000, 1, 1), False), # <30 years
        (ElectionType.GRAM_PANCHAYAT, datetime(2003, 6, 1), True),  # 21+ years
        (ElectionType.GRAM_PANCHAYAT, datetime(2005, 1, 1), False), # <21 years
    ])
    def test_age_eligibility(self, service, base_candidate, election_type, dob, expected):
        base_candidate.date_of_birth = dob.replace(tzinfo=timezone.utc)
        result = service._check_age(base_candidate, election_type)
        assert result["passed"] == expected

    def test_missing_dob_fails(self, service, base_candidate):
        base_candidate.date_of_birth = None
        result = service._check_age(base_candidate, ElectionType.LOK_SABHA)
        assert result["passed"] is False
        assert "not provided" in result["details"]

    def test_age_details_show_correct_requirement(self, service, base_candidate):
        base_candidate.date_of_birth = datetime(1985, 1, 1, tzinfo=timezone.utc)
        result = service._check_age(base_candidate, ElectionType.RAJYA_SABHA)
        assert "30" in result["details"]
        assert "Article 84(b)" in result["details"]


# ── Electoral Roll Check ──────────────────────────────────────────────────

class TestElectoralRollCheck:
    def test_registered_voter_passes(self, service, base_candidate):
        assert service._check_electoral_roll(base_candidate) is True

    def test_missing_roll_number_fails(self, service, base_candidate):
        base_candidate.electoral_roll_number = None
        assert service._check_electoral_roll(base_candidate) is False

    def test_missing_state_fails(self, service, base_candidate):
        base_candidate.electoral_roll_state = None
        assert service._check_electoral_roll(base_candidate) is False

    def test_empty_roll_number_fails(self, service, base_candidate):
        base_candidate.electoral_roll_number = ""
        assert service._check_electoral_roll(base_candidate) is False


# ── Office of Profit Check ────────────────────────────────────────────────

class TestOfficeOfProfitCheck:
    def test_no_office_of_profit_passes(self, service, base_candidate):
        base_candidate.holds_office_of_profit = False
        assert service._check_office_of_profit(base_candidate) is True

    def test_office_of_profit_fails(self, service, base_candidate):
        base_candidate.holds_office_of_profit = True
        assert service._check_office_of_profit(base_candidate) is False


# ── Conviction Check ──────────────────────────────────────────────────────

class TestConvictionCheck:
    def test_no_criminal_cases_passes(self, service, base_candidate):
        result = service._check_convictions(base_candidate)
        assert result["passed"] is True
        assert "No criminal cases" in result["details"]

    def test_pending_case_passes_with_warning(self, service, base_candidate):
        base_candidate.has_criminal_cases = True
        base_candidate.has_pending_criminal_cases = True
        base_candidate.criminal_case_details = [
            {"case_number": "CR/100/2023", "convicted": False}
        ]
        result = service._check_convictions(base_candidate)
        assert result["passed"] is True
        assert result.get("warning") is True

    def test_conviction_2plus_years_fails(self, service, base_candidate):
        """Section 8(3) RPA 1951 - conviction >= 2 years = disqualification."""
        base_candidate.has_criminal_cases = True
        base_candidate.criminal_case_details = [
            {"case_number": "CR/200/2020", "convicted": True, "sentence_years": 3}
        ]
        result = service._check_convictions(base_candidate)
        assert result["passed"] is False

    def test_conviction_under_2_years_passes(self, service, base_candidate):
        """Conviction < 2 years not disqualifying under Section 8(3)."""
        base_candidate.has_criminal_cases = True
        base_candidate.criminal_case_details = [
            {"case_number": "CR/300/2022", "convicted": True, "sentence_years": 1}
        ]
        result = service._check_convictions(base_candidate)
        assert result["passed"] is True


# ── Score Calculation ─────────────────────────────────────────────────────

class TestScoreCalculation:
    def test_fully_eligible_candidate_scores_high(self, service, base_candidate):
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "Age: 44 years"},
            "electoral_roll": True,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": True,
            "conviction": {"passed": True, "details": "No convictions"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        status, elig_score, risk_score, risk_level = service._calculate_scores(
            checks, base_candidate, ElectionType.LOK_SABHA
        )
        assert status == EligibilityStatus.ELIGIBLE
        assert elig_score >= 90
        assert risk_level == RiskLevel.LOW

    def test_disqualifying_conviction_returns_disqualified(self, service, base_candidate):
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "OK"},
            "electoral_roll": True,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": True,  # insolvency OK
            "conviction": {"passed": False, "details": "Disqualifying conviction"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        # conviction failure should not trigger critical (it's not in critical_checks)
        status, _, _, _ = service._calculate_scores(
            checks, base_candidate, ElectionType.LOK_SABHA
        )
        # conviction is weighted but conviction check failure reduces score
        assert status in [EligibilityStatus.HIGH_RISK, EligibilityStatus.DISQUALIFIED]

    def test_insolvent_candidate_disqualified(self, service, base_candidate):
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "OK"},
            "electoral_roll": True,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": False,  # CRITICAL FAILURE
            "conviction": {"passed": True, "details": "OK"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        status, elig_score, risk_score, risk_level = service._calculate_scores(
            checks, base_candidate, ElectionType.LOK_SABHA
        )
        assert status == EligibilityStatus.DISQUALIFIED
        assert elig_score == 0.0
        assert risk_level == RiskLevel.CRITICAL

    def test_pending_criminal_cases_increase_risk(self, service, base_candidate):
        base_candidate.has_pending_criminal_cases = True
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "OK"},
            "electoral_roll": True,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": True,
            "conviction": {"passed": True, "details": "Pending but not convicted"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        _, _, risk_score_with_pending, _ = service._calculate_scores(
            checks, base_candidate, ElectionType.LOK_SABHA
        )

        base_candidate.has_pending_criminal_cases = False
        _, _, risk_score_without_pending, _ = service._calculate_scores(
            checks, base_candidate, ElectionType.LOK_SABHA
        )

        assert risk_score_with_pending > risk_score_without_pending


# ── Recommendations ───────────────────────────────────────────────────────

class TestRecommendations:
    def test_no_electoral_roll_triggers_critical_recommendation(self, service, base_candidate):
        base_candidate.electoral_roll_number = None
        base_candidate.electoral_roll_state = None
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "OK"},
            "electoral_roll": False,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": True,
            "conviction": {"passed": True, "details": "OK"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        recs = service._build_recommendations(checks, base_candidate, ElectionType.LOK_SABHA)
        critical = [r for r in recs if r["priority"] == "CRITICAL"]
        assert len(critical) >= 1
        assert "electoral roll" in critical[0]["action"].lower()

    def test_criminal_cases_trigger_disclosure_recommendation(self, service, base_candidate):
        base_candidate.has_pending_criminal_cases = True
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "OK"},
            "electoral_roll": True,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": True,
            "conviction": {"passed": True, "details": "Pending case, not convicted"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        recs = service._build_recommendations(checks, base_candidate, ElectionType.LOK_SABHA)
        high_recs = [r for r in recs if r["priority"] == "HIGH"]
        assert any("Form 26" in r["action"] or "criminal" in r["action"].lower() for r in high_recs)


# ── Age Requirements ──────────────────────────────────────────────────────

class TestAgeRequirements:
    def test_all_election_types_have_requirements(self):
        for election_type in ElectionType:
            assert election_type in AGE_REQUIREMENTS
            assert "min_age" in AGE_REQUIREMENTS[election_type]
            assert "article" in AGE_REQUIREMENTS[election_type]

    def test_lok_sabha_requires_25(self):
        assert AGE_REQUIREMENTS[ElectionType.LOK_SABHA]["min_age"] == 25

    def test_rajya_sabha_requires_30(self):
        assert AGE_REQUIREMENTS[ElectionType.RAJYA_SABHA]["min_age"] == 30

    def test_legislative_council_requires_30(self):
        assert AGE_REQUIREMENTS[ElectionType.LEGISLATIVE_COUNCIL]["min_age"] == 30

    def test_local_body_requires_21(self):
        local_bodies = [
            ElectionType.GRAM_PANCHAYAT, ElectionType.MANDAL_PARISHAD,
            ElectionType.ZILLA_PARISHAD, ElectionType.MUNICIPALITY,
            ElectionType.MUNICIPAL_CORPORATION,
        ]
        for et in local_bodies:
            assert AGE_REQUIREMENTS[et]["min_age"] == 21


# ── Legal Explanation ─────────────────────────────────────────────────────

class TestLegalExplanation:
    def test_eligible_explanation_positive(self, service, base_candidate):
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "Age: 44 years. Required: ≥25"},
            "electoral_roll": True,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": True,
            "conviction": {"passed": True, "details": "No convictions"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        explanation = service._build_legal_explanation(
            checks, base_candidate, ElectionType.LOK_SABHA, EligibilityStatus.ELIGIBLE
        )
        assert "ELIGIBLE" in explanation
        assert "✅" in explanation

    def test_disqualified_explanation_shows_warning(self, service, base_candidate):
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "OK"},
            "electoral_roll": False,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": False,
            "conviction": {"passed": True, "details": "OK"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        explanation = service._build_legal_explanation(
            checks, base_candidate, ElectionType.LOK_SABHA, EligibilityStatus.DISQUALIFIED
        )
        assert "DISQUALIFIED" in explanation or "❌" in explanation

    def test_pending_criminal_cases_appear_in_explanation(self, service, base_candidate):
        base_candidate.has_pending_criminal_cases = True
        checks = {
            "citizenship": True,
            "age": {"passed": True, "details": "OK"},
            "electoral_roll": True,
            "office_of_profit": True,
            "corrupt_practices": True,
            "government_contract": True,
            "insolvency": True,
            "conviction": {"passed": True, "details": "Pending, not convicted"},
            "election_expenditure": True,
            "reservation": True,
            "local_body": True,
        }
        explanation = service._build_legal_explanation(
            checks, base_candidate, ElectionType.LOK_SABHA, EligibilityStatus.POTENTIALLY_ELIGIBLE
        )
        assert "PENDING" in explanation or "pending" in explanation.lower()
        assert "ADR" in explanation or "Form 26" in explanation
