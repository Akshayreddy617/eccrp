"""
ECCRP Module 7 - Election Expenditure Tracker
Tracks, categorises, and risk-rates campaign expenditure.
"""

from uuid import UUID
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import structlog

from app.db.session import get_db
from app.db.models import User, Expenditure, Election, ExpenditureCategory, RiskLevel
from app.core.security import get_current_active_user
from app.schemas import ExpenditureCreateRequest, ExpenditureDashboardResponse

router = APIRouter()
logger = structlog.get_logger(__name__)


def _calculate_expenditure_risk(
    total_spent: float, expenditure_limit: Optional[float]
) -> RiskLevel:
    if not expenditure_limit:
        return RiskLevel.LOW
    pct = (total_spent / expenditure_limit) * 100
    if pct >= 95:
        return RiskLevel.CRITICAL
    elif pct >= 85:
        return RiskLevel.HIGH
    elif pct >= 70:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _build_risk_alerts(
    total_spent: float,
    expenditure_limit: Optional[float],
    by_category: list,
) -> List[str]:
    alerts = []
    if expenditure_limit:
        pct = (total_spent / expenditure_limit) * 100
        if pct >= 95:
            alerts.append(
                f"🔴 CRITICAL: {pct:.1f}% of expenditure limit utilised. "
                "Exceeding limit leads to disqualification under Section 10A RPA 1951."
            )
        elif pct >= 85:
            alerts.append(f"🟠 HIGH: {pct:.1f}% of expenditure limit used. Slow down spending.")
        elif pct >= 70:
            alerts.append(f"🟡 MEDIUM: {pct:.1f}% of limit utilised. Monitor closely.")

    # Digital ad specific check (ECI rules on digital advertising)
    for cat in by_category:
        if cat["category"] == ExpenditureCategory.ADVERTISING_DIGITAL.value and cat["total"] > 100000:
            alerts.append(
                "⚠️ Digital advertising spend >₹1 lakh requires pre-certification from ECI. "
                "Ref: ECI's MCMC guidelines on digital media."
            )
    return alerts


@router.post("/", status_code=201)
async def add_expenditure(
    payload: ExpenditureCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a new expenditure entry."""
    expenditure = Expenditure(
        candidate_id=payload.candidate_id,
        election_id=payload.election_id,
        category=payload.category,
        description=payload.description,
        amount=Decimal(str(payload.amount)),
        expense_date=payload.expense_date,
        vendor_name=payload.vendor_name,
        vendor_pan=payload.vendor_pan,
        receipt_number=payload.receipt_number,
        notes=payload.notes,
    )
    db.add(expenditure)
    await db.flush()
    await db.refresh(expenditure)
    logger.info("expenditure_added", amount=payload.amount, category=payload.category.value)
    return {"id": str(expenditure.id), "message": "Expenditure recorded successfully"}


@router.get("/dashboard/{candidate_id}/{election_id}", response_model=ExpenditureDashboardResponse)
async def get_expenditure_dashboard(
    candidate_id: UUID,
    election_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 7: Expenditure Dashboard

    Returns total spent, limit utilization, category breakdown,
    daily trend, and risk alerts.
    """
    # Get election expenditure limit
    election_result = await db.execute(
        select(Election).where(Election.id == election_id)
    )
    election: Election = election_result.scalar_one_or_none()
    expenditure_limit = float(election.expenditure_limit) if election and election.expenditure_limit else None

    # Total spent
    total_result = await db.execute(
        select(func.sum(Expenditure.amount)).where(
            Expenditure.candidate_id == candidate_id,
            Expenditure.election_id == election_id,
        )
    )
    total_spent = float(total_result.scalar() or 0)

    # By category
    cat_result = await db.execute(
        select(
            Expenditure.category,
            func.sum(Expenditure.amount).label("total"),
            func.count(Expenditure.id).label("count"),
        )
        .where(
            Expenditure.candidate_id == candidate_id,
            Expenditure.election_id == election_id,
        )
        .group_by(Expenditure.category)
        .order_by(desc("total"))
    )
    by_category = [
        {
            "category": row.category.value,
            "total": float(row.total),
            "count": row.count,
            "percentage": round((float(row.total) / total_spent * 100), 2) if total_spent > 0 else 0,
        }
        for row in cat_result.all()
    ]

    # Daily trend (last 30 days)
    daily_result = await db.execute(
        select(
            func.date_trunc("day", Expenditure.expense_date).label("day"),
            func.sum(Expenditure.amount).label("daily_total"),
        )
        .where(
            Expenditure.candidate_id == candidate_id,
            Expenditure.election_id == election_id,
        )
        .group_by("day")
        .order_by("day")
        .limit(30)
    )
    daily_trend = [
        {"date": str(row.day.date()), "amount": float(row.daily_total)}
        for row in daily_result.all()
    ]

    # Recent entries
    recent_result = await db.execute(
        select(Expenditure)
        .where(
            Expenditure.candidate_id == candidate_id,
            Expenditure.election_id == election_id,
        )
        .order_by(desc(Expenditure.expense_date))
        .limit(10)
    )
    recent_entries = [
        {
            "id": str(e.id),
            "category": e.category.value,
            "description": e.description,
            "amount": float(e.amount),
            "expense_date": str(e.expense_date.date()),
            "vendor_name": e.vendor_name,
        }
        for e in recent_result.scalars().all()
    ]

    limit_pct = round((total_spent / expenditure_limit * 100), 2) if expenditure_limit else None
    risk_level = _calculate_expenditure_risk(total_spent, expenditure_limit)
    risk_alerts = _build_risk_alerts(total_spent, expenditure_limit, by_category)

    return ExpenditureDashboardResponse(
        candidate_id=candidate_id,
        election_id=election_id,
        expenditure_limit=expenditure_limit,
        total_spent=total_spent,
        limit_utilization_pct=limit_pct,
        risk_level=risk_level,
        by_category=by_category,
        daily_trend=daily_trend,
        risk_alerts=risk_alerts,
        recent_entries=recent_entries,
    )


@router.get("/{candidate_id}/{election_id}/entries")
async def list_expenditure_entries(
    candidate_id: UUID,
    election_id: UUID,
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all expenditure entries with pagination."""
    query = select(Expenditure).where(
        Expenditure.candidate_id == candidate_id,
        Expenditure.election_id == election_id,
    )
    if category:
        query = query.where(Expenditure.category == category)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(desc(Expenditure.expense_date))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": str(e.id),
                "category": e.category.value,
                "description": e.description,
                "amount": float(e.amount),
                "expense_date": str(e.expense_date),
                "vendor_name": e.vendor_name,
                "vendor_pan": e.vendor_pan,
                "receipt_number": e.receipt_number,
                "is_disputed": e.is_disputed,
            }
            for e in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.delete("/{expenditure_id}", status_code=204)
async def delete_expenditure(
    expenditure_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an expenditure entry."""
    result = await db.execute(
        select(Expenditure).where(Expenditure.id == expenditure_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Expenditure entry not found")
    await db.delete(entry)
