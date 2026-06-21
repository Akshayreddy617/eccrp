"""ECCRP Module 14 - Consultant Dashboard."""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models import (
    User, Candidate, EligibilityCheck, RiskAssessment,
    NominationReadiness, Notification, UserRole
)
from app.core.security import get_current_active_user
from app.schemas import ConsultantDashboardResponse, CandidateSummaryCard

router = APIRouter()


@router.get("/consultant", response_model=ConsultantDashboardResponse)
async def get_consultant_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 14: Consultant Dashboard.
    Shows all candidates, compliance status, pending actions, risk levels, readiness scores.
    """
    # For admin/consultant: all candidates; for candidates: only their own
    if current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CONSULTANT]:
        candidates_result = await db.execute(
            select(Candidate).where(Candidate.is_active == True).limit(100)
        )
    else:
        candidates_result = await db.execute(
            select(Candidate).where(
                Candidate.user_id == current_user.id, Candidate.is_active == True
            )
        )
    candidates = candidates_result.scalars().all()

    candidate_cards = []
    for c in candidates:
        # Get latest eligibility check
        elig_result = await db.execute(
            select(EligibilityCheck)
            .where(EligibilityCheck.candidate_id == c.id, EligibilityCheck.is_latest == True)
            .limit(1)
        )
        elig = elig_result.scalar_one_or_none()

        # Get latest risk assessment
        risk_result = await db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.candidate_id == c.id, RiskAssessment.is_latest == True)
            .limit(1)
        )
        risk = risk_result.scalar_one_or_none()

        # Get readiness
        ready_result = await db.execute(
            select(NominationReadiness).where(NominationReadiness.candidate_id == c.id).limit(1)
        )
        readiness = ready_result.scalar_one_or_none()

        # Build pending actions
        pending_actions = []
        if not elig:
            pending_actions.append("Run eligibility check")
        if not readiness or readiness.overall_readiness_score < 100:
            pending_actions.append("Complete nomination documents")
        if not risk:
            pending_actions.append("Generate risk assessment")
        if c.has_pending_criminal_cases and not c.criminal_case_details:
            pending_actions.append("Add criminal case details for disclosure")

        candidate_cards.append({
            "candidate_id": str(c.id),
            "candidate_name": c.full_name,
            "party_affiliation": c.party_affiliation,
            "eligibility_status": elig.eligibility_status.value if elig else None,
            "eligibility_score": elig.eligibility_score if elig else None,
            "overall_risk": risk.overall_risk.value if risk else None,
            "overall_risk_score": risk.overall_risk_score if risk else None,
            "readiness_score": readiness.overall_readiness_score if readiness else 0.0,
            "pending_actions": pending_actions,
            "pending_actions_count": len(pending_actions),
        })

    # Unread notifications
    notif_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id, Notification.is_read == False
        )
    )
    unread_notifications = notif_result.scalar() or 0

    return ConsultantDashboardResponse(
        total_candidates=len(candidates),
        active_elections=0,  # Would query active elections
        pending_actions_count=sum(c["pending_actions_count"] for c in candidate_cards),
        candidates=candidate_cards,
    )


@router.get("/notifications")
async def get_notifications(
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get notifications for current user."""
    from sqlalchemy import desc
    query = select(Notification).where(Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    query = query.order_by(desc(Notification.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "type": n.notification_type,
            "priority": n.priority,
            "is_read": n.is_read,
            "created_at": str(n.created_at),
        }
        for n in notifications
    ]


@router.post("/notifications/{notification_id}/read", status_code=204)
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a notification as read."""
    from datetime import datetime, timezone
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    )
    notif = result.scalar_one_or_none()
    if notif:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
