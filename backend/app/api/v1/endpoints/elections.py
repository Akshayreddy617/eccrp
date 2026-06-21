"""ECCRP Elections Endpoints - Module 1 Election Selection Engine."""

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User, Election, State, Constituency, ElectionType
from app.core.security import get_current_active_user
from app.schemas import (
    ElectionCreateRequest, ElectionResponse,
    ElectionSelectionRequest, ElectionSelectionResponse,
)

router = APIRouter()

# ── Legal provisions loaded per election type ───────────────────────────────
from app.services.eligibility_service import ELECTION_TYPE_PROVISIONS, KEY_JUDGMENTS


@router.post("/select", response_model=ElectionSelectionResponse)
async def select_election(
    payload: ElectionSelectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 1: Election Selection Engine.

    User selects election type, state, district, constituency.
    System auto-loads all applicable constitutional provisions,
    election laws, SEC rules, and relevant judgments.
    """
    # Load state
    state_result = await db.execute(
        select(State).where(State.code == payload.state_code.upper())
    )
    state = state_result.scalar_one_or_none()
    state_name = state.name if state else payload.state_code

    provisions = ELECTION_TYPE_PROVISIONS.get(payload.election_type, {})
    applicable_articles = provisions.get("constitution_articles", [])
    applicable_sections = provisions.get("rp_act_sections", [])

    # SEC rules are state-specific
    sec_rules = []
    if state:
        sec_rules = [
            {
                "rule": f"{state.sec_name or 'State Election Commission'} Rules",
                "note": "Download from respective State Election Commission portal",
                "applicable_to": payload.election_type.value,
            }
        ]

    # Find constituency if specified
    constituency_details = None
    if payload.constituency_name:
        const_result = await db.execute(
            select(Constituency).where(
                Constituency.name.ilike(f"%{payload.constituency_name}%"),
                Constituency.election_type == payload.election_type,
            ).limit(1)
        )
        const = const_result.scalar_one_or_none()
        if const:
            constituency_details = {
                "id": str(const.id),
                "name": const.name,
                "number": const.number,
                "reservation_category": const.reservation_category,
                "total_voters": const.total_voters,
            }

    return ElectionSelectionResponse(
        election_type=payload.election_type,
        state=state_name,
        applicable_provisions=applicable_articles,
        applicable_laws=applicable_sections,
        applicable_sec_rules=sec_rules,
        applicable_judgments=KEY_JUDGMENTS,
        constituency_details=constituency_details,
    )


@router.post("/", response_model=ElectionResponse, status_code=201)
async def create_election(
    payload: ElectionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create an election record."""
    election = Election(**payload.dict())
    db.add(election)
    await db.flush()
    await db.refresh(election)
    return election


@router.get("/", response_model=List[ElectionResponse])
async def list_elections(
    election_type: Optional[ElectionType] = Query(None),
    year: Optional[int] = Query(None),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List elections with optional filters."""
    query = select(Election).where(Election.is_active == is_active)
    if election_type:
        query = query.where(Election.election_type == election_type)
    if year:
        query = query.where(Election.year == year)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{election_id}", response_model=ElectionResponse)
async def get_election(
    election_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Election).where(Election.id == election_id))
    election = result.scalar_one_or_none()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")
    return election
