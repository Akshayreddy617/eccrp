"""ECCRP Module 5 - Compliance Risk Engine."""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.db.models import User, RiskAssessment, RiskLevel, EligibilityCheck, Affidavit, Expenditure, MCCCheck, Election
from app.core.security import get_current_active_user
from app.schemas import RiskAssessmentResponse

router = APIRouter()


async def _compute_risk_assessment(
    db: AsyncSession,
    candidate_id: UUID,
    election_id: Optional[UUID],
) -> RiskAssessment:
    """Aggregate all risk signals into a unified risk assessment."""

    # 1. Eligibility risk
    elig_result = await db.execute(
        select(EligibilityCheck)
        .where(EligibilityCheck.candidate_id == candidate_id, EligibilityCheck.is_latest == True)
        .limit(1)
    )
    elig = elig_result.scalar_one_or_none()
    elig_risk_score = (elig.risk_score or 0.0) if elig else 50.0
    elig_risk_level = elig.risk_level if elig else RiskLevel.MEDIUM
    elig_factors = (elig.recommendations or []) if elig else [{"action": "Run eligibility check"}]

    # 2. Disclosure risk (from affidavit)
    disc_risk_score = 0.0
    disc_risk_factors = []
    if election_id:
        aff_result = await db.execute(
            select(Affidavit)
            .where(Affidavit.candidate_id == candidate_id, Affidavit.election_id == election_id)
            .order_by(desc(Affidavit.created_at)).limit(1)
        )
        aff = aff_result.scalar_one_or_none()
        if aff:
            missing_count = len(aff.missing_fields or [])
            inconsistency_count = len(aff.inconsistencies or [])
            disc_risk_score = min(100.0, (missing_count * 15) + (inconsistency_count * 10))
            disc_risk_factors = (aff.potential_legal_risks or [])
        else:
            disc_risk_score = 60.0
            disc_risk_factors = [{"risk": "Affidavit not filed", "legal_basis": "Section 33A RPA 1951"}]

    disc_risk_level = _score_to_level(disc_risk_score)

    # 3. Legal risk (from pending criminal cases on eligibility check)
    legal_risk_score = 0.0
    legal_risk_factors = []
    if elig:
        if not elig.conviction_check:
            legal_risk_score = 95.0
            legal_risk_factors = [{"risk": "Disqualifying conviction", "legal_basis": "Section 8(3) RPA 1951"}]
        elif elig.conviction_details:
            legal_risk_score = 60.0
            legal_risk_factors = [{"risk": "Pending criminal cases require mandatory disclosure"}]

    legal_risk_level = _score_to_level(legal_risk_score)

    # 4. Expenditure risk
    exp_risk_score = 0.0
    exp_risk_factors = []
    if election_id:
        from sqlalchemy import func
        exp_result = await db.execute(
            select(func.sum(Expenditure.amount))
            .where(Expenditure.candidate_id == candidate_id, Expenditure.election_id == election_id)
        )
        total_spent = float(exp_result.scalar() or 0)

        election_result = await db.execute(select(Election).where(Election.id == election_id))
        election = election_result.scalar_one_or_none()
        if election and election.expenditure_limit:
            pct = (total_spent / float(election.expenditure_limit)) * 100
            if pct >= 95:
                exp_risk_score = 95.0
                exp_risk_factors = [{"risk": f"Expenditure at {pct:.1f}% of limit — near disqualification threshold under Section 10A RPA 1951"}]
            elif pct >= 80:
                exp_risk_score = 70.0
                exp_risk_factors = [{"risk": f"Expenditure at {pct:.1f}% of limit"}]

    exp_risk_level = _score_to_level(exp_risk_score)

    # 5. MCC risk
    mcc_risk_score = 0.0
    mcc_risk_factors = []
    if election_id:
        mcc_result = await db.execute(
            select(MCCCheck)
            .where(MCCCheck.candidate_id == candidate_id, MCCCheck.election_id == election_id)
            .order_by(desc(MCCCheck.created_at)).limit(5)
        )
        mcc_checks = mcc_result.scalars().all()
        from app.db.models import MCCStatus
        violations = [c for c in mcc_checks if c.mcc_status == MCCStatus.VIOLATION]
        potential = [c for c in mcc_checks if c.mcc_status == MCCStatus.POTENTIAL_VIOLATION]
        mcc_risk_score = min(100.0, (len(violations) * 30) + (len(potential) * 15))
        if violations:
            mcc_risk_factors = [{"risk": f"{len(violations)} MCC violation(s) detected", "legal_basis": "ECI MCC Guidelines"}]

    mcc_risk_level = _score_to_level(mcc_risk_score)

    # Overall risk = weighted average
    overall_score = round(
        (elig_risk_score * 0.30) +
        (disc_risk_score * 0.20) +
        (legal_risk_score * 0.25) +
        (exp_risk_score * 0.15) +
        (mcc_risk_score * 0.10), 2
    )
    overall_level = _score_to_level(overall_score)

    # Priority actions
    priority_actions = []
    for factor in elig_factors[:2]:
        if isinstance(factor, dict):
            priority_actions.append({"source": "eligibility", **factor})

    # Mark old assessments as non-latest
    from sqlalchemy import update
    await db.execute(
        update(RiskAssessment)
        .where(RiskAssessment.candidate_id == candidate_id, RiskAssessment.is_latest == True)
        .values(is_latest=False)
    )

    assessment = RiskAssessment(
        candidate_id=candidate_id,
        election_id=election_id,
        eligibility_risk=elig_risk_level,
        eligibility_risk_score=round(elig_risk_score, 2),
        eligibility_risk_factors=elig_factors,
        disclosure_risk=disc_risk_level,
        disclosure_risk_score=round(disc_risk_score, 2),
        disclosure_risk_factors=disc_risk_factors,
        legal_risk=legal_risk_level,
        legal_risk_score=round(legal_risk_score, 2),
        legal_risk_factors=legal_risk_factors,
        expenditure_risk=exp_risk_level,
        expenditure_risk_score=round(exp_risk_score, 2),
        expenditure_risk_factors=exp_risk_factors,
        mcc_risk=mcc_risk_level,
        mcc_risk_score=round(mcc_risk_score, 2),
        mcc_risk_factors=mcc_risk_factors,
        overall_risk=overall_level,
        overall_risk_score=overall_score,
        executive_summary=_build_summary(overall_level, overall_score),
        priority_actions=priority_actions,
        is_latest=True,
    )
    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)
    return assessment


def _score_to_level(score: float) -> RiskLevel:
    if score >= 80:
        return RiskLevel.CRITICAL
    elif score >= 60:
        return RiskLevel.HIGH
    elif score >= 30:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _build_summary(level: RiskLevel, score: float) -> str:
    summaries = {
        RiskLevel.CRITICAL: f"⛔ CRITICAL RISK ({score:.0f}/100): Immediate legal intervention required. High probability of disqualification or election petition.",
        RiskLevel.HIGH: f"🔴 HIGH RISK ({score:.0f}/100): Significant compliance gaps detected. Urgent corrective action needed before nomination.",
        RiskLevel.MEDIUM: f"🟡 MEDIUM RISK ({score:.0f}/100): Several compliance items need attention. Addressable with proper legal guidance.",
        RiskLevel.LOW: f"✅ LOW RISK ({score:.0f}/100): Candidate appears well-positioned. Continue monitoring as election progresses.",
    }
    return summaries.get(level, "Risk assessment complete.")


@router.post("/assess/{candidate_id}", response_model=RiskAssessmentResponse, status_code=201)
async def generate_risk_assessment(
    candidate_id: UUID,
    election_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 5: Generate comprehensive compliance risk assessment.

    Aggregates signals from: Eligibility, Disclosure, Legal, Expenditure, MCC.
    Returns risk scores across all 5 dimensions plus overall risk level.
    """
    assessment = await _compute_risk_assessment(db, candidate_id, election_id)
    return assessment


@router.get("/candidate/{candidate_id}/latest", response_model=RiskAssessmentResponse)
async def get_latest_risk_assessment(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the latest risk assessment for a candidate."""
    result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.candidate_id == candidate_id, RiskAssessment.is_latest == True)
        .limit(1)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="No risk assessment found. Run POST /assess/{candidate_id} first.")
    return assessment
