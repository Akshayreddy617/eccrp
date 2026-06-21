"""ECCRP Admin Endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models import User, AuditLog, UserRole, LegalRule, Judgment, KnowledgeArticle
from app.core.security import require_admin, get_current_active_user

router = APIRouter()


@router.get("/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: Get platform-wide statistics."""
    from app.db.models import Candidate, Election, EligibilityCheck, MCCCheck, AIQueryLog

    stats = {}
    for model, key in [
        (User, "total_users"),
        (Candidate, "total_candidates"),
        (Election, "total_elections"),
        (EligibilityCheck, "total_eligibility_checks"),
        (MCCCheck, "total_mcc_checks"),
        (LegalRule, "total_legal_rules"),
        (Judgment, "total_judgments"),
        (AIQueryLog, "total_ai_queries"),
    ]:
        result = await db.execute(select(func.count(model.id)))
        stats[key] = result.scalar() or 0

    return stats


@router.get("/users")
async def list_users(
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: List all users."""
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "created_at": str(u.created_at),
        }
        for u in users
    ]


@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: Activate or deactivate a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    return {"user_id": str(user.id), "is_active": user.is_active}


@router.get("/audit-logs")
async def get_audit_logs(
    resource_type: str = None,
    user_id: UUID = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: View audit logs."""
    from sqlalchemy import desc
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "user_id": str(l.user_id) if l.user_id else None,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": str(l.resource_id) if l.resource_id else None,
            "ip_address": l.ip_address,
            "status": l.status,
            "created_at": str(l.created_at),
        }
        for l in logs
    ]


@router.post("/seed/judgments")
async def seed_landmark_judgments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: Seed landmark SC judgments into the database."""
    from app.api.v1.endpoints.judgments import LANDMARK_JUDGMENTS

    created = 0
    for j_data in LANDMARK_JUDGMENTS:
        existing = await db.execute(
            select(Judgment).where(Judgment.case_name == j_data["case_name"])
        )
        if not existing.scalar_one_or_none():
            judgment = Judgment(**j_data)
            db.add(judgment)
            created += 1

    await db.flush()
    return {"message": f"Seeded {created} landmark judgments", "total": len(LANDMARK_JUDGMENTS)}


@router.post("/ingest/legal-corpus")
async def trigger_legal_corpus_ingestion(
    _: User = Depends(require_admin),
):
    """Admin: Trigger legal corpus ingestion into OpenSearch (async job)."""
    # In production this would queue a Celery task
    return {
        "message": "Legal corpus ingestion queued",
        "note": "This runs as a background job. Check /admin/stats for progress.",
    }
