"""
ECCRP Module 8 - Model Code of Conduct Checker
AI-powered MCC violation detection with legal citations.
"""

from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import structlog

from app.db.session import get_db
from app.db.models import User, MCCCheck, MCCStatus
from app.core.security import get_current_active_user
from app.schemas import MCCCheckRequest, MCCCheckResponse
from app.services.mcc_service import MCCService

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/check", response_model=MCCCheckResponse, status_code=201)
async def check_mcc_compliance(
    payload: MCCCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 8: Model Code of Conduct Checker

    User describes a campaign activity. System checks against:
    - ECI MCC Guidelines
    - State-specific rules
    - Supreme Court interpretations

    Returns: Compliant / Potential Violation / Violation with citations.

    Example activities to check:
    - "Distributing sarees to voters in Anantapur on polling day eve"
    - "Publishing an advertisement attacking the ruling party's record"
    - "Using a government bus for campaign rally"
    - "Organizing a biryani distribution event two days before polling"
    """
    service = MCCService(db)
    result = await service.check_activity(
        payload=payload,
        checked_by_user_id=current_user.id,
    )
    return result


@router.get("/election/{election_id}/history", response_model=List[MCCCheckResponse])
async def get_mcc_check_history(
    election_id: UUID,
    candidate_id: Optional[UUID] = Query(None),
    status_filter: Optional[MCCStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get MCC check history for an election."""
    query = select(MCCCheck).where(MCCCheck.election_id == election_id)
    if candidate_id:
        query = query.where(MCCCheck.candidate_id == candidate_id)
    if status_filter:
        query = query.where(MCCCheck.mcc_status == status_filter)
    query = query.order_by(desc(MCCCheck.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/rules", summary="Get MCC Rules Reference")
async def get_mcc_rules(
    election_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    """Get reference list of MCC rules and ECI guidelines."""
    from app.services.mcc_service import MCC_RULES_REFERENCE
    rules = MCC_RULES_REFERENCE
    return {"total": len(rules), "rules": rules}
