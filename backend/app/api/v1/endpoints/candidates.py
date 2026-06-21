"""ECCRP Candidate Endpoints - CRUD operations."""

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.session import get_db
from app.db.models import User, Candidate
from app.core.security import get_current_active_user
from app.schemas import CandidateCreateRequest, CandidateUpdateRequest, CandidateResponse

router = APIRouter()


@router.post("/", response_model=CandidateResponse, status_code=201)
async def create_candidate(
    payload: CandidateCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new candidate profile."""
    candidate = Candidate(user_id=current_user.id, **payload.dict())
    db.add(candidate)
    await db.flush()
    await db.refresh(candidate)
    return candidate


@router.get("/", response_model=List[CandidateResponse])
async def list_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all candidates accessible to the current user."""
    query = select(Candidate).where(Candidate.is_active == True)
    if search:
        query = query.where(Candidate.full_name.ilike(f"%{search}%"))
    query = query.order_by(Candidate.full_name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: UUID,
    payload: CandidateUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(candidate, field, value)
    await db.flush()
    await db.refresh(candidate)
    return candidate


@router.delete("/{candidate_id}", status_code=204)
async def deactivate_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.is_active = False
