"""ECCRP Module 9 - Legal Knowledge Repository."""

from uuid import UUID
from typing import List, Optional
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.db.session import get_db
from app.db.models import User, LegalRule, KnowledgeArticle
from app.core.security import get_current_active_user
from app.schemas import LegalRuleResponse, KnowledgeSearchRequest, KnowledgeSearchResponse

router = APIRouter()


@router.get("/rules", response_model=List[LegalRuleResponse])
async def list_legal_rules(
    source_type: Optional[str] = Query(None),
    election_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List legal rules with optional filters."""
    query = select(LegalRule).where(LegalRule.is_active == True)
    if source_type:
        query = query.where(LegalRule.source_type == source_type)
    if search:
        query = query.where(
            or_(
                LegalRule.title.ilike(f"%{search}%"),
                LegalRule.section_number.ilike(f"%{search}%"),
                LegalRule.summary.ilike(f"%{search}%"),
            )
        )
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/rules/{rule_id}")
async def get_legal_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific legal rule with full text."""
    result = await db.execute(select(LegalRule).where(LegalRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Legal rule not found")
    return {
        "id": str(rule.id),
        "source_type": rule.source_type.value if rule.source_type else None,
        "section_number": rule.section_number,
        "title": rule.title,
        "full_text": rule.full_text,
        "summary": rule.summary,
        "applicable_election_types": rule.applicable_election_types,
        "keywords": rule.keywords,
    }


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Full-text search across the legal knowledge base.
    Searches: legal rules, knowledge articles, ECI circulars.
    """
    start = time.perf_counter()

    # DB full-text search (fallback when OpenSearch not available)
    query = select(LegalRule).where(
        or_(
            LegalRule.title.ilike(f"%{payload.query}%"),
            LegalRule.full_text.ilike(f"%{payload.query}%"),
            LegalRule.summary.ilike(f"%{payload.query}%"),
        )
    ).limit(payload.limit)

    if payload.election_type:
        query = query.where(
            LegalRule.applicable_election_types.contains([payload.election_type.value])
        )

    result = await db.execute(query)
    rules = result.scalars().all()

    results = [
        {
            "type": "legal_rule",
            "id": str(r.id),
            "title": r.title,
            "section": r.section_number,
            "source_type": r.source_type.value if r.source_type else None,
            "summary": r.summary,
        }
        for r in rules
    ]

    elapsed_ms = (time.perf_counter() - start) * 1000
    return KnowledgeSearchResponse(
        query=payload.query,
        results=results,
        total=len(results),
        search_time_ms=round(elapsed_ms, 2),
    )


@router.get("/articles")
async def list_knowledge_articles(
    article_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List published knowledge articles."""
    query = select(KnowledgeArticle).where(KnowledgeArticle.is_published == True)
    if article_type:
        query = query.where(KnowledgeArticle.article_type == article_type)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    articles = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "slug": a.slug,
            "article_type": a.article_type.value if a.article_type else None,
            "summary": a.summary,
            "tags": a.tags,
            "published_at": str(a.published_at) if a.published_at else None,
        }
        for a in articles
    ]
