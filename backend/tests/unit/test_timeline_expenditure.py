"""ECCRP Unit Tests - Timeline and Expenditure."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from app.db.models import Election, ElectionType, RiskLevel
from app.api.v1.endpoints.timeline import _build_timeline_actions
from app.api.v1.endpoints.expenditure import _calculate_expenditure_risk, _build_risk_alerts


def make_election(**kwargs):
    base = dict(
        id=uuid4(),
        constituency_id=uuid4(),
        election_type=ElectionType.LOK_SABHA,
        name="Test Election",
        year=2024,
        expenditure_limit=7500000,
        is_active=True,
    )
    base.update(kwargs)
    e = Election()
    for k, v in base.items():
        setattr(e, k, v)
    return e


class TestTimeline:
    def test_timeline_with_all_dates(self):
        now = datetime.now(timezone.utc)
        election = make_election(
            notification_date=now - timedelta(days=30),
            nomination_start_date=now - timedelta(days=20),
            nomination_end_date=now - timedelta(days=15),
            nomination_scrutiny_date=now - timedelta(days=14),
            withdrawal_date=now - timedelta(days=12),
            polling_date=now + timedelta(days=5),
            counting_date=now + timedelta(days=8),
            result_date=now + timedelta(days=8),
        )
        actions = _build_timeline_actions(election)
        assert len(actions) > 0

    def test_timeline_contains_critical_deadlines(self):
        now = datetime.now(timezone.utc)
        election = make_election(
            nomination_end_date=now + timedelta(days=3),
            withdrawal_date=now + timedelta(days=7),
            polling_date=now + timedelta(days=14),
            result_date=now + timedelta(days=17),
        )
        actions = _build_timeline_actions(election)
        titles = [a["title"] for a in actions]
        assert any("Nomination" in t for t in titles)
        assert any("Expenditure" in t or "30 day" in t.lower() or "30-day" in t.lower() or "File" in t for t in titles)

    def test_expenditure_deadline_30_days_after_result(self):
        now = datetime.now(timezone.utc)
        result_date = now + timedelta(days=20)
        election = make_election(result_date=result_date)
        actions = _build_timeline_actions(election)
        exp_actions = [a for a in actions if "Expenditure" in a["title"] or "expenditure" in a["description"].lower()]
        assert len(exp_actions) > 0
        # Deadline should be 30 days after result
        exp_deadline_date = (result_date + timedelta(days=30)).date()
        assert any(a["date"] == str(exp_deadline_date) for a in exp_actions)

    def test_campaign_silence_48hrs_before_polling(self):
        now = datetime.now(timezone.utc)
        polling_date = now + timedelta(days=10)
        election = make_election(
            withdrawal_date=now + timedelta(days=2),
            polling_date=polling_date,
        )
        actions = _build_timeline_actions(election)
        silence_actions = [a for a in actions if "silence" in a["title"].lower() or "48" in a["title"]]
        assert len(silence_actions) > 0

    def test_actions_sorted_by_date(self):
        now = datetime.now(timezone.utc)
        election = make_election(
            notification_date=now - timedelta(days=10),
            nomination_end_date=now + timedelta(days=5),
            polling_date=now + timedelta(days=20),
            result_date=now + timedelta(days=23),
        )
        actions = _build_timeline_actions(election)
        dates = [a["date"] for a in actions]
        assert dates == sorted(dates)

    def test_timeline_empty_dates_graceful(self):
        election = make_election()
        actions = _build_timeline_actions(election)
        assert isinstance(actions, list)


class TestExpenditureRisk:
    def test_low_utilization_is_low_risk(self):
        assert _calculate_expenditure_risk(1000000, 7500000) == RiskLevel.LOW

    def test_70_percent_is_medium_risk(self):
        assert _calculate_expenditure_risk(5250000, 7500000) == RiskLevel.MEDIUM

    def test_85_percent_is_high_risk(self):
        assert _calculate_expenditure_risk(6375000, 7500000) == RiskLevel.HIGH

    def test_95_percent_is_critical_risk(self):
        assert _calculate_expenditure_risk(7125000, 7500000) == RiskLevel.CRITICAL

    def test_no_limit_is_low_risk(self):
        assert _calculate_expenditure_risk(5000000, None) == RiskLevel.LOW

    def test_zero_spend_is_low_risk(self):
        assert _calculate_expenditure_risk(0, 7500000) == RiskLevel.LOW

    def test_risk_alerts_critical(self):
        alerts = _build_risk_alerts(7200000, 7500000, [])
        assert len(alerts) > 0
        assert any("CRITICAL" in a or "95" in a for a in alerts)

    def test_risk_alerts_high(self):
        alerts = _build_risk_alerts(6500000, 7500000, [])
        assert len(alerts) > 0

    def test_no_alerts_when_low(self):
        alerts = _build_risk_alerts(1000000, 7500000, [])
        assert len(alerts) == 0

    def test_digital_ad_alert_triggered(self):
        by_category = [{"category": "advertising_digital", "total": 150000}]
        alerts = _build_risk_alerts(150000, 7500000, by_category)
        digital_alerts = [a for a in alerts if "digital" in a.lower() or "MCMC" in a]
        assert len(digital_alerts) > 0

    def test_digital_ad_no_alert_below_threshold(self):
        by_category = [{"category": "advertising_digital", "total": 50000}]
        alerts = _build_risk_alerts(50000, 7500000, by_category)
        digital_alerts = [a for a in alerts if "MCMC" in a]
        assert len(digital_alerts) == 0
