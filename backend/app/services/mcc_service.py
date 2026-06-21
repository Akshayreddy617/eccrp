"""
ECCRP MCC Service
Business logic for Module 8 - Model Code of Conduct Checker.
Rule-based + AI-assisted violation detection.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.models import MCCCheck, MCCStatus
from app.schemas import MCCCheckRequest
from app.core.config import settings

logger = structlog.get_logger(__name__)

# ── MCC Rules Reference ────────────────────────────────────────────────────

MCC_RULES_REFERENCE = [
    {
        "id": "MCC-GEN-01",
        "category": "General Conduct",
        "rule": "No party or candidate shall include in any activity which may aggravate existing differences or create mutual hatred or cause tension between different castes and communities, religious or linguistic.",
        "source": "ECI MCC Part I Clause 1",
        "violation_type": "communal",
    },
    {
        "id": "MCC-GEN-02",
        "category": "Meetings & Rallies",
        "rule": "The party or candidate shall inform the local police authorities of the venue and time of proposed meetings to enable them to make adequate arrangements.",
        "source": "ECI MCC Part II Clause 1",
        "violation_type": "procedural",
    },
    {
        "id": "MCC-GEN-03",
        "category": "Processions",
        "rule": "The organising party shall provide volunteers with distinctive badges for marshalling processions. Prior permission from police must be obtained.",
        "source": "ECI MCC Part III",
        "violation_type": "procedural",
    },
    {
        "id": "MCC-BRIBE-01",
        "category": "Bribery",
        "rule": "No distribution of liquor, cash, gifts, or articles to voters. Bribery is a cognizable offence under Section 171B IPC and Section 123(1) RPA 1951.",
        "source": "ECI MCC Part VI; Section 123(1) RPA 1951; Section 171B IPC",
        "violation_type": "bribery",
        "severity": "critical",
    },
    {
        "id": "MCC-GOVT-01",
        "category": "Government Machinery",
        "rule": "Ministers and other authorities shall not use official machinery or personnel for party or election work.",
        "source": "ECI MCC Part VII Clause 1",
        "violation_type": "government_machinery",
        "severity": "high",
    },
    {
        "id": "MCC-GOVT-02",
        "category": "Government Vehicles",
        "rule": "Government transport shall not be used for campaign purposes. No government accommodation to be used as campaign office.",
        "source": "ECI MCC Part VII Clause 3",
        "violation_type": "government_machinery",
        "severity": "high",
    },
    {
        "id": "MCC-POLL-01",
        "category": "Polling Day",
        "rule": "No campaign within 48 hours of polling. No movement of voters through vehicles except those authorised by ECI.",
        "source": "Section 126 RPA 1951; ECI Circular 2019",
        "violation_type": "polling_day",
        "severity": "critical",
    },
    {
        "id": "MCC-ADV-01",
        "category": "Advertisements",
        "rule": "All political advertisements on electronic media must be pre-certified by the Media Certification & Monitoring Committee (MCMC).",
        "source": "ECI Circular No. 509/75/2004/JS-I; Section 126A RPA 1951",
        "violation_type": "advertisement",
        "severity": "high",
    },
    {
        "id": "MCC-ADV-02",
        "category": "Digital Advertising",
        "rule": "All paid political advertisements on social media and digital platforms must be pre-certified. Platforms must maintain a public ad library.",
        "source": "ECI Guidelines on Internet and Social Media 2019; IT (Amendment) Rules 2021",
        "violation_type": "digital_advertisement",
        "severity": "high",
    },
    {
        "id": "MCC-POLL-02",
        "category": "Exit Polls",
        "rule": "Conducting, publishing, or publicising exit polls during the period notified by ECI is prohibited.",
        "source": "Section 126A RPA 1951",
        "violation_type": "polling_day",
        "severity": "high",
    },
    {
        "id": "MCC-HATE-01",
        "category": "Hate Speech",
        "rule": "No appeal to voters on grounds of religion, race, caste, community, or language. Using religion or caste for canvassing is a corrupt practice.",
        "source": "Section 123(3) RPA 1951; ECI MCC Part I",
        "violation_type": "hate_speech",
        "severity": "critical",
    },
    {
        "id": "MCC-STAR-01",
        "category": "Star Campaigners",
        "rule": "Star campaigners' expenses are not included in candidate's expenditure only if they campaign for multiple constituencies. Single constituency = included.",
        "source": "ECI Circular; Section 77 RPA 1951",
        "violation_type": "expenditure",
        "severity": "medium",
    },
]

# ── Keyword-to-rule mapping for fast detection ─────────────────────────────

KEYWORD_RULE_MAP = {
    # Bribery triggers
    "saree": ("MCC-BRIBE-01", MCCStatus.VIOLATION),
    "cash distribution": ("MCC-BRIBE-01", MCCStatus.VIOLATION),
    "biryani": ("MCC-BRIBE-01", MCCStatus.POTENTIAL_VIOLATION),
    "liquor": ("MCC-BRIBE-01", MCCStatus.VIOLATION),
    "alcohol": ("MCC-BRIBE-01", MCCStatus.VIOLATION),
    "gift": ("MCC-BRIBE-01", MCCStatus.POTENTIAL_VIOLATION),
    "distribute food": ("MCC-BRIBE-01", MCCStatus.POTENTIAL_VIOLATION),
    "free meal": ("MCC-BRIBE-01", MCCStatus.POTENTIAL_VIOLATION),
    "money to voter": ("MCC-BRIBE-01", MCCStatus.VIOLATION),

    # Government machinery
    "government bus": ("MCC-GOVT-02", MCCStatus.VIOLATION),
    "government vehicle": ("MCC-GOVT-02", MCCStatus.VIOLATION),
    "official car": ("MCC-GOVT-02", MCCStatus.VIOLATION),
    "government helicopter": ("MCC-GOVT-02", MCCStatus.VIOLATION),
    "minister campaigning": ("MCC-GOVT-01", MCCStatus.POTENTIAL_VIOLATION),
    "government office": ("MCC-GOVT-01", MCCStatus.POTENTIAL_VIOLATION),

    # Advertisement
    "tv advertisement": ("MCC-ADV-01", MCCStatus.POTENTIAL_VIOLATION),
    "television ad": ("MCC-ADV-01", MCCStatus.POTENTIAL_VIOLATION),
    "radio advertisement": ("MCC-ADV-01", MCCStatus.POTENTIAL_VIOLATION),
    "digital ad": ("MCC-ADV-02", MCCStatus.POTENTIAL_VIOLATION),
    "facebook ad": ("MCC-ADV-02", MCCStatus.POTENTIAL_VIOLATION),
    "youtube advertisement": ("MCC-ADV-02", MCCStatus.POTENTIAL_VIOLATION),
    "instagram ad": ("MCC-ADV-02", MCCStatus.POTENTIAL_VIOLATION),

    # Polling day
    "polling day": ("MCC-POLL-01", MCCStatus.POTENTIAL_VIOLATION),
    "election day": ("MCC-POLL-01", MCCStatus.POTENTIAL_VIOLATION),
    "48 hours": ("MCC-POLL-01", MCCStatus.POTENTIAL_VIOLATION),
    "exit poll": ("MCC-POLL-02", MCCStatus.VIOLATION),

    # Hate speech
    "caste appeal": ("MCC-HATE-01", MCCStatus.VIOLATION),
    "religion appeal": ("MCC-HATE-01", MCCStatus.VIOLATION),
    "vote for hindu": ("MCC-HATE-01", MCCStatus.VIOLATION),
    "vote for muslim": ("MCC-HATE-01", MCCStatus.VIOLATION),
    "temple visit": ("MCC-HATE-01", MCCStatus.POTENTIAL_VIOLATION),
    "mosque visit": ("MCC-HATE-01", MCCStatus.POTENTIAL_VIOLATION),
}

SEVERITY_MAP = {
    "critical": 0.95,
    "high": 0.80,
    "medium": 0.65,
    "low": 0.50,
}


class MCCService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _rule_based_check(self, description: str) -> tuple[MCCStatus, list, list]:
        """Fast keyword-based MCC violation detection."""
        desc_lower = description.lower()
        triggered_rules = []
        worst_status = MCCStatus.COMPLIANT
        status_order = [MCCStatus.COMPLIANT, MCCStatus.POTENTIAL_VIOLATION, MCCStatus.VIOLATION]

        for keyword, (rule_id, status) in KEYWORD_RULE_MAP.items():
            if keyword in desc_lower:
                rule = next((r for r in MCC_RULES_REFERENCE if r["id"] == rule_id), None)
                if rule and rule_id not in [r["id"] for r in triggered_rules]:
                    triggered_rules.append(rule)
                    if status_order.index(status) > status_order.index(worst_status):
                        worst_status = status

        return worst_status, triggered_rules, []

    async def _ai_enhanced_check(
        self, description: str, rule_based_status: MCCStatus, triggered_rules: list
    ) -> tuple[str, float, str]:
        """Use LLM to provide detailed analysis if AI is configured."""
        if not settings.OPENAI_API_KEY:
            # Fallback to rule-based only
            if not triggered_rules:
                details = "No obvious MCC violations detected by rule-based analysis. Manual review recommended."
                action = "Proceed with caution. Consult election lawyer for edge cases."
            else:
                details = f"Detected {len(triggered_rules)} potential rule violation(s): {', '.join(r['category'] for r in triggered_rules)}."
                action = "Stop the activity immediately and consult your election law counsel."
            return details, 0.75, action

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY,
            )

            rules_context = "\n".join([
                f"- {r['id']}: {r['rule']} [Source: {r['source']}]"
                for r in MCC_RULES_REFERENCE
            ])

            prompt = f"""You are an Indian election law expert specializing in the Model Code of Conduct.

Analyze this campaign activity for MCC violations:
"{description}"

Pre-detected rule triggers: {[r['id'] for r in triggered_rules]}

MCC Rules Reference:
{rules_context}

Respond in exactly this format:
VIOLATION_DETAILS: [Specific violation analysis]
RECOMMENDED_ACTION: [Concrete action to take]
CONFIDENCE: [0.0-1.0]
CITATION: [Specific ECI guideline, section, or circular number]"""

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse response
            details = self._extract_field(content, "VIOLATION_DETAILS")
            action = self._extract_field(content, "RECOMMENDED_ACTION")
            confidence_str = self._extract_field(content, "CONFIDENCE")
            citation = self._extract_field(content, "CITATION")

            try:
                confidence = float(confidence_str)
            except (ValueError, TypeError):
                confidence = 0.75

            if citation and citation not in details:
                details = f"{details}\n\nLegal Citation: {citation}"

            return details, confidence, action

        except Exception as e:
            logger.warning("mcc_ai_check_failed", error=str(e))
            return (
                f"Activity description analyzed. {len(triggered_rules)} rule(s) triggered.",
                0.65,
                "Review with election counsel before proceeding.",
            )

    def _extract_field(self, text: str, field: str) -> str:
        """Extract a field from LLM response."""
        lines = text.split("\n")
        for line in lines:
            if line.startswith(f"{field}:"):
                return line[len(f"{field}:"):].strip()
        return ""

    async def check_activity(
        self,
        payload: MCCCheckRequest,
        checked_by_user_id: UUID,
    ) -> MCCCheck:
        """Run full MCC check: rule-based + AI-enhanced."""

        # Step 1: Rule-based check
        rule_status, triggered_rules, _ = self._rule_based_check(payload.activity_description)

        # Step 2: AI-enhanced analysis
        violation_details, confidence, recommended_action = await self._ai_enhanced_check(
            payload.activity_description, rule_status, triggered_rules
        )

        # Step 3: Build citation lists
        applicable_mcc_rules = [
            {
                "id": r["id"],
                "category": r["category"],
                "rule": r["rule"],
                "severity": r.get("severity", "medium"),
            }
            for r in triggered_rules
        ]

        eci_circular_refs = list({
            r["source"] for r in triggered_rules if "ECI" in r.get("source", "") or "Section" in r.get("source", "")
        })

        # Determine violation category
        violation_category = None
        if triggered_rules:
            categories = list({r.get("violation_type", "general") for r in triggered_rules})
            violation_category = ", ".join(categories)

        # Build ECI refs
        eci_refs = [
            {"source": src, "description": "Refer to full ECI guideline document"}
            for src in eci_circular_refs[:5]
        ]

        check = MCCCheck(
            election_id=payload.election_id,
            candidate_id=payload.candidate_id,
            checked_by_user_id=checked_by_user_id,
            activity_description=payload.activity_description,
            activity_type=payload.activity_type,
            activity_date=payload.activity_date,
            activity_location=payload.activity_location,
            mcc_status=rule_status,
            violation_category=violation_category,
            violation_details=violation_details if rule_status != MCCStatus.COMPLIANT else None,
            applicable_mcc_rules=applicable_mcc_rules,
            eci_circular_refs=eci_refs,
            state_rules_refs=[],
            recommended_action=recommended_action,
            ai_confidence_score=confidence,
        )

        self.db.add(check)
        await self.db.flush()
        await self.db.refresh(check)

        logger.info(
            "mcc_check_completed",
            status=rule_status.value,
            rules_triggered=len(triggered_rules),
            confidence=confidence,
        )
        return check
