"""
ECCRP Module 2 - Eligibility Assessment Engine
Determines candidate eligibility for any election type.
"""

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.db.models import User, EligibilityCheck, Candidate
from app.core.security import get_current_active_user
from app.schemas import EligibilityCheckRequest, EligibilityCheckResponse
from app.services.eligibility_service import EligibilityService

router = APIRouter()


@router.post("/check", response_model=EligibilityCheckResponse, status_code=201)
async def run_eligibility_check(
    payload: EligibilityCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 2: Run a full eligibility assessment for a candidate.

    Checks:
    - Citizenship (Article 84 / Article 173)
    - Age requirements per election type
    - Electoral roll registration
    - Office of Profit (Article 102 / Article 191)
    - Corrupt Practices (Section 8A RPA 1951)
    - Government Contracts (Section 9A RPA 1951)
    - Insolvency (Section 9 RPA 1951)
    - Convictions (Section 8 RPA 1951)
    - Election Expenditure Violations (Section 10A RPA 1951)
    - Reservation eligibility
    - Local body specific eligibility
    """
    service = EligibilityService(db)
    result = await service.run_full_check(
        candidate_id=payload.candidate_id,
        election_type=payload.election_type,
        state_id=payload.state_id,
        election_id=payload.election_id,
        checked_by_user_id=current_user.id,
    )
    return result


@router.get("/candidate/{candidate_id}", response_model=List[EligibilityCheckResponse])
async def get_candidate_eligibility_history(
    candidate_id: UUID,
    election_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get eligibility check history for a candidate."""
    query = (
        select(EligibilityCheck)
        .where(EligibilityCheck.candidate_id == candidate_id)
        .order_by(desc(EligibilityCheck.created_at))
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/candidate/{candidate_id}/latest", response_model=EligibilityCheckResponse)
async def get_latest_eligibility(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the most recent eligibility check for a candidate."""
    result = await db.execute(
        select(EligibilityCheck)
        .where(
            EligibilityCheck.candidate_id == candidate_id,
            EligibilityCheck.is_latest == True,
        )
        .order_by(desc(EligibilityCheck.created_at))
        .limit(1)
    )
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="No eligibility check found for this candidate")
    return check


@router.get("/{check_id}", response_model=EligibilityCheckResponse)
async def get_eligibility_check(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific eligibility check by ID."""
    result = await db.execute(
        select(EligibilityCheck).where(EligibilityCheck.id == check_id)
    )
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Eligibility check not found")
    return check
