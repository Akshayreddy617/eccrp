"""ECCRP Module 10 - Supreme Court Judgment Library."""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc

from app.db.session import get_db
from app.db.models import User, Judgment, JudgmentMapping, LegalRule
from app.core.security import get_current_active_user
from app.schemas import JudgmentResponse, JudgmentImpactResponse

router = APIRouter()

# ── Landmark judgments seed data ────────────────────────────────────────────
LANDMARK_JUDGMENTS = [
    {
        "case_name": "Association for Democratic Reforms v. Union of India",
        "citation": "(2002) 5 SCC 294",
        "year": 2002,
        "court": "Supreme Court of India",
        "bench_composition": "3-Judge Bench",
        "issue": "Whether voters have the right to know criminal antecedents, assets and liabilities of candidates",
        "ratio_decidendi": "Voters have a fundamental right under Article 19(1)(a) to know about the criminal antecedents, assets, liabilities and educational qualifications of candidates. ECI directed to collect and disseminate this information through affidavit.",
        "impact_summary": "Established mandatory affidavit disclosure for all candidates. Led to Form 26 requirement under Section 33A RPA 1951.",
        "relevant_sections": [{"section": "33A", "act": "RPA 1951"}, {"article": "19(1)(a)", "act": "Constitution"}],
        "affected_election_types": ["lok_sabha", "rajya_sabha", "legislative_assembly", "legislative_council"],
        "is_landmark": True,
    },
    {
        "case_name": "Lily Thomas v. Union of India",
        "citation": "(2013) 7 SCC 653",
        "year": 2013,
        "court": "Supreme Court of India",
        "bench_composition": "2-Judge Bench",
        "issue": "Whether a sitting MP/MLA convicted with sentence of 2+ years is instantly disqualified",
        "ratio_decidendi": "Section 8(4) RPA 1951 (which allowed 3-month protection to sitting members) is unconstitutional. Conviction with ≥2 years sentence leads to immediate disqualification regardless of appeal.",
        "impact_summary": "Eliminated the 3-month protection for sitting legislators. Any conviction with ≥2 years sentence = immediate disqualification. Appeal does not stay disqualification.",
        "relevant_sections": [{"section": "8(3)", "act": "RPA 1951"}, {"section": "8(4) struck down", "act": "RPA 1951"}],
        "affected_election_types": ["lok_sabha", "rajya_sabha", "legislative_assembly", "legislative_council"],
        "is_landmark": True,
    },
    {
        "case_name": "Public Interest Foundation v. Union of India",
        "citation": "(2019) 3 SCC 224",
        "year": 2019,
        "court": "Supreme Court of India",
        "bench_composition": "5-Judge Constitution Bench",
        "issue": "Whether persons charged with serious offences should be barred from contesting elections",
        "ratio_decidendi": "Court stopped short of disqualifying those merely charged (pending cases). However, directed Parliament to legislate. Political parties must mandatorily publish reasons for fielding candidates with criminal cases on party website, in newspapers, and through social media within 48 hours of candidate selection.",
        "impact_summary": "Enhanced transparency requirement for political parties. Mandatory publication of criminal antecedents and reasons for fielding such candidates.",
        "relevant_sections": [{"section": "8", "act": "RPA 1951"}, {"article": "324", "act": "Constitution"}],
        "affected_election_types": ["lok_sabha", "rajya_sabha", "legislative_assembly"],
        "is_landmark": True,
    },
    {
        "case_name": "People's Union for Civil Liberties v. Union of India (NOTA)",
        "citation": "(2013) 10 SCC 1",
        "year": 2013,
        "court": "Supreme Court of India",
        "bench_composition": "2-Judge Bench",
        "issue": "Right of voters to reject all candidates (NOTA)",
        "ratio_decidendi": "Negative voting (NOTA) is a fundamental right under Article 19(1)(a). ECI directed to provide NOTA option on EVMs.",
        "impact_summary": "Introduction of NOTA (None Of The Above) option in Indian elections. Strengthens voter's right of expression.",
        "relevant_sections": [{"article": "19(1)(a)", "act": "Constitution"}, {"section": "79(d)", "act": "RPA 1951"}],
        "affected_election_types": ["lok_sabha", "legislative_assembly"],
        "is_landmark": True,
    },
    {
        "case_name": "Kuldip Nayar v. Union of India",
        "citation": "(2006) 7 SCC 1",
        "year": 2006,
        "court": "Supreme Court of India",
        "bench_composition": "5-Judge Constitution Bench",
        "issue": "Validity of open ballot system for Rajya Sabha elections; domicile requirement",
        "ratio_decidendi": "Removal of domicile requirement for Rajya Sabha candidates is constitutionally valid. Open ballot in RS elections is valid to curb cross-voting.",
        "impact_summary": "Clarified that Rajya Sabha candidates need not be residents of the state they represent. Open voting in RS elections upheld.",
        "relevant_sections": [{"article": "80", "act": "Constitution"}, {"section": "59", "act": "RPA 1951"}],
        "affected_election_types": ["rajya_sabha"],
        "is_landmark": True,
    },
    {
        "case_name": "Indira Nehru Gandhi v. Raj Narain",
        "citation": "AIR 1975 SC 2299",
        "year": 1975,
        "court": "Supreme Court of India",
        "bench_composition": "5-Judge Constitution Bench",
        "issue": "Validity of election of Indira Gandhi; scope of election law; doctrine of free and fair elections",
        "ratio_decidendi": "Free and fair elections are a basic feature of the Constitution. Parliament cannot retrospectively validate a void election. Strict interpretation of corrupt practices provisions.",
        "impact_summary": "Established free and fair elections as a basic feature of the Constitution. Landmark in election jurisprudence. Led to 39th Constitutional Amendment later struck down.",
        "relevant_sections": [{"article": "329B", "act": "Constitution (subsequently struck down)"}, {"section": "123", "act": "RPA 1951"}],
        "affected_election_types": ["lok_sabha"],
        "is_landmark": True,
    },
]


@router.get("/", response_model=List[JudgmentResponse])
async def list_judgments(
    year: Optional[int] = Query(None),
    is_landmark: Optional[bool] = Query(None),
    election_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Module 10: List Supreme Court judgments with filters."""
    query = select(Judgment)
    if year:
        query = query.where(Judgment.year == year)
    if is_landmark is not None:
        query = query.where(Judgment.is_landmark == is_landmark)
    if search:
        query = query.where(
            or_(
                Judgment.case_name.ilike(f"%{search}%"),
                Judgment.issue.ilike(f"%{search}%"),
                Judgment.ratio_decidendi.ilike(f"%{search}%"),
            )
        )
    query = query.order_by(desc(Judgment.year)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/landmarks")
async def get_landmark_judgments(
    current_user: User = Depends(get_current_active_user),
):
    """Get all landmark election judgments (pre-seeded reference data)."""
    return {"total": len(LANDMARK_JUDGMENTS), "judgments": LANDMARK_JUDGMENTS}


@router.get("/{judgment_id}", response_model=JudgmentResponse)
async def get_judgment(
    judgment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Judgment).where(Judgment.id == judgment_id))
    judgment = result.scalar_one_or_none()
    if not judgment:
        raise HTTPException(status_code=404, detail="Judgment not found")
    return judgment


@router.get("/{judgment_id}/impact", response_model=List[dict])
async def get_judgment_impact(
    judgment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Module 11: Get compliance requirements mapped from this judgment."""
    result = await db.execute(
        select(JudgmentMapping).where(JudgmentMapping.judgment_id == judgment_id)
    )
    mappings = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "mapping_type": m.mapping_type,
            "compliance_requirement": m.compliance_requirement,
            "triggered_by": m.triggered_by,
            "notes": m.notes,
        }
        for m in mappings
    ]


@router.get("/impact/scenario")
async def get_judgment_impact_by_scenario(
    scenario: str = Query(..., description="Describe the candidate's situation"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 11: Judgment Impact Engine.
    Given a candidate scenario, returns applicable law → judgment → compliance requirement chain.
    """
    scenario_lower = scenario.lower()

    # Rule-based scenario matching
    impacts = []

    if any(word in scenario_lower for word in ["criminal", "case", "conviction", "fir", "arrested"]):
        impacts.append({
            "scenario": scenario,
            "applicable_law": {"section": "8(3)", "act": "Representation of the People Act 1951"},
            "relevant_judgment": {
                "case_name": "Lily Thomas v. Union of India",
                "citation": "(2013) 7 SCC 653",
                "year": 2013,
            },
            "compliance_requirement": "Disclose ALL pending criminal cases in Form 26 (Affidavit). If convicted with ≥2 years sentence, candidate is immediately disqualified.",
            "recommended_action": "File complete affidavit with criminal case details. If convicted, do NOT file nomination.",
        })

    if any(word in scenario_lower for word in ["asset", "property", "wealth", "income"]):
        impacts.append({
            "scenario": scenario,
            "applicable_law": {"section": "33A", "act": "Representation of the People Act 1951"},
            "relevant_judgment": {
                "case_name": "Association for Democratic Reforms v. Union of India",
                "citation": "(2002) 5 SCC 294",
                "year": 2002,
            },
            "compliance_requirement": "Disclose all assets (movable and immovable) of self, spouse, and dependents in Form 26. Non-disclosure can lead to election petition.",
            "recommended_action": "Prepare comprehensive asset disclosure covering all family members. Ensure PAN is linked.",
        })

    if any(word in scenario_lower for word in ["expenditure", "expense", "spend", "cost", "campaign cost"]):
        impacts.append({
            "scenario": scenario,
            "applicable_law": {"section": "77, 78, 10A", "act": "Representation of the People Act 1951"},
            "relevant_judgment": {
                "case_name": "Kanwar Lal Gupta v. Amar Nath Chawla",
                "citation": "AIR 1975 SC 308",
                "year": 1975,
            },
            "compliance_requirement": "All election expenditure must be recorded in a separate register from date of nomination. Account to be filed within 30 days of election results.",
            "recommended_action": "Maintain day-wise expense ledger. Appoint election agent. File account on time to avoid Section 10A disqualification.",
        })

    if not impacts:
        impacts.append({
            "scenario": scenario,
            "applicable_law": {"section": "Multiple", "act": "RPA 1951 / Constitution of India"},
            "relevant_judgment": None,
            "compliance_requirement": "Use the AI Assistant for detailed analysis of this specific scenario.",
            "recommended_action": "Consult election counsel and use ECCRP AI Governance Assistant for detailed guidance.",
        })

    return impacts
