"""ECCRP Module 15 - Public Transparency Portal (no auth required)."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.db.session import get_db
from app.db.models import Candidate, Affidavit, ElectionParticipation, Election

router = APIRouter()


@router.get("/candidates")
async def search_public_candidates(
    name: Optional[str] = Query(None, description="Candidate name"),
    constituency: Optional[str] = Query(None),
    party: Optional[str] = Query(None),
    election_year: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Module 15: Public Transparency Portal - Search candidates.
    No authentication required. Shows only publicly declared information.
    """
    query = select(Candidate).where(Candidate.is_active == True)
    if name:
        query = query.where(Candidate.full_name.ilike(f"%{name}%"))
    if party:
        query = query.where(Candidate.party_affiliation.ilike(f"%{party}%"))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    candidates = result.scalars().all()

    return {
        "results": [
            {
                "id": str(c.id),
                "full_name": c.full_name,
                "party_affiliation": c.party_affiliation,
                "is_independent": c.is_independent,
                "education": c.education_qualification,
                "has_criminal_cases": c.has_criminal_cases,
                "has_pending_criminal_cases": c.has_pending_criminal_cases,
            }
            for c in candidates
        ],
        "total": len(candidates),
        "page": page,
    }


@router.get("/candidates/{candidate_id}/disclosures")
async def get_public_disclosures(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Module 15: Public disclosure view for a candidate.
    Shows publicly available affidavit data (assets, liabilities, criminal cases).
    """
    cand_result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = cand_result.scalar_one_or_none()
    if not candidate:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Get latest affidavit
    from sqlalchemy import desc
    aff_result = await db.execute(
        select(Affidavit)
        .where(Affidavit.candidate_id == candidate_id)
        .order_by(desc(Affidavit.created_at))
        .limit(1)
    )
    affidavit = aff_result.scalar_one_or_none()

    # Get election history
    part_result = await db.execute(
        select(ElectionParticipation).where(ElectionParticipation.candidate_id == candidate_id)
    )
    participations = part_result.scalars().all()

    return {
        "candidate": {
            "id": str(candidate.id),
            "full_name": candidate.full_name,
            "party_affiliation": candidate.party_affiliation,
            "education": candidate.education_qualification,
            "occupation": candidate.occupation,
        },
        "disclosures": {
            "has_criminal_cases": candidate.has_criminal_cases,
            "has_pending_criminal_cases": candidate.has_pending_criminal_cases,
            "criminal_cases_count": len(candidate.criminal_case_details or []),
            "assets_movable": affidavit.assets_movable if affidavit else None,
            "assets_immovable": affidavit.assets_immovable if affidavit else None,
            "liabilities": affidavit.liabilities if affidavit else None,
            "criminal_cases": affidavit.criminal_cases if affidavit else [],
            "affidavit_date": str(affidavit.created_at.date()) if affidavit else None,
        },
        "election_history": [
            {
                "election_id": str(p.election_id),
                "nomination_filed": p.nomination_filed,
                "final_status": p.final_status,
                "votes_polled": p.votes_polled,
            }
            for p in participations
        ],
        "data_source": "Publicly declared affidavit data (Form 26) as required by Section 33A RPA 1951",
        "disclaimer": "This data is sourced from candidate affidavits. ECCRP does not verify the accuracy of self-declared information.",
    }
