"""ECCRP Unit Tests - MCC Service."""
import pytest
from unittest.mock import AsyncMock
from app.db.models import MCCStatus
from app.services.mcc_service import MCCService, KEYWORD_RULE_MAP, MCC_RULES_REFERENCE

@pytest.fixture
def service():
    return MCCService(AsyncMock())

class TestRuleBasedCheck:
    def test_saree_distribution_is_violation(self, service):
        status, rules, _ = service._rule_based_check("Distributing sarees to voters in Tirupati")
        assert status == MCCStatus.VIOLATION
        assert any(r["id"] == "MCC-BRIBE-01" for r in rules)

    def test_government_vehicle_is_violation(self, service):
        status, rules, _ = service._rule_based_check("Using government bus for campaign rally")
        assert status == MCCStatus.VIOLATION
        assert any(r["id"] == "MCC-GOVT-02" for r in rules)

    def test_exit_poll_is_violation(self, service):
        status, rules, _ = service._rule_based_check("Conducting exit poll on polling day")
        assert status == MCCStatus.VIOLATION
        assert any(r["id"] == "MCC-POLL-02" for r in rules)

    def test_digital_ad_is_potential_violation(self, service):
        status, rules, _ = service._rule_based_check("Publishing a Facebook ad for the candidate")
        assert status == MCCStatus.POTENTIAL_VIOLATION
        assert any(r["id"] == "MCC-ADV-02" for r in rules)

    def test_clean_activity_is_compliant(self, service):
        status, rules, _ = service._rule_based_check("Holding a press conference at party office")
        assert status == MCCStatus.COMPLIANT
        assert len(rules) == 0

    def test_liquor_distribution_is_violation(self, service):
        status, rules, _ = service._rule_based_check("Distributing liquor to supporters before election")
        assert status == MCCStatus.VIOLATION

    def test_biryani_is_potential_violation(self, service):
        status, rules, _ = service._rule_based_check("Organizing biryani distribution at rally")
        assert status == MCCStatus.POTENTIAL_VIOLATION

    def test_minister_campaigning_is_potential(self, service):
        status, rules, _ = service._rule_based_check("Minister campaigning using official vehicle")
        assert status in [MCCStatus.POTENTIAL_VIOLATION, MCCStatus.VIOLATION]

    def test_worst_status_wins(self, service):
        """When multiple rules triggered, worst status should win."""
        status, rules, _ = service._rule_based_check(
            "Distributing sarees and conducting exit poll"
        )
        assert status == MCCStatus.VIOLATION

class TestMCCRulesReference:
    def test_all_rules_have_required_fields(self):
        for rule in MCC_RULES_REFERENCE:
            assert "id" in rule
            assert "category" in rule
            assert "rule" in rule
            assert "source" in rule
            assert "violation_type" in rule

    def test_bribery_rule_exists(self):
        bribery_rules = [r for r in MCC_RULES_REFERENCE if r["violation_type"] == "bribery"]
        assert len(bribery_rules) >= 1

    def test_hate_speech_rule_exists(self):
        hate_rules = [r for r in MCC_RULES_REFERENCE if r["violation_type"] == "hate_speech"]
        assert len(hate_rules) >= 1

    def test_polling_day_rule_exists(self):
        poll_rules = [r for r in MCC_RULES_REFERENCE if r["violation_type"] == "polling_day"]
        assert len(poll_rules) >= 1

    def test_keyword_map_references_valid_rules(self):
        rule_ids = {r["id"] for r in MCC_RULES_REFERENCE}
        for keyword, (rule_id, status) in KEYWORD_RULE_MAP.items():
            assert rule_id in rule_ids, f"Keyword '{keyword}' references unknown rule '{rule_id}'"

    def test_all_statuses_valid(self):
        valid_statuses = set(MCCStatus)
        for keyword, (rule_id, status) in KEYWORD_RULE_MAP.items():
            assert status in valid_statuses

class TestExtractField:
    def test_extract_existing_field(self, service):
        text = "VIOLATION_DETAILS: This is a violation\nRECOMMENDED_ACTION: Stop immediately"
        result = service._extract_field(text, "VIOLATION_DETAILS")
        assert result == "This is a violation"

    def test_extract_missing_field_returns_empty(self, service):
        text = "SOME_OTHER_FIELD: value"
        result = service._extract_field(text, "VIOLATION_DETAILS")
        assert result == ""

    def test_extract_confidence(self, service):
        text = "CONFIDENCE: 0.85"
        result = service._extract_field(text, "CONFIDENCE")
        assert float(result) == 0.85
