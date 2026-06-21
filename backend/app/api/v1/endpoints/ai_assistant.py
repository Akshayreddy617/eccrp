"""
ECCRP Module 12 - AI Governance Assistant Endpoint
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.session import get_db
from app.db.models import User, AIQueryLog
from app.core.security import get_current_active_user
from app.schemas import AIQueryRequest, AIQueryResponse
from app.ai.rag.engine import ECCRPRagEngine
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)

_rag_engine: ECCRPRagEngine | None = None


def get_rag_engine() -> ECCRPRagEngine:
    global _rag_engine
    if _rag_engine is None:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="AI service not configured. OPENAI_API_KEY is missing.",
            )
        _rag_engine = ECCRPRagEngine()
    return _rag_engine


@router.post("/query", response_model=AIQueryResponse)
async def query_ai_assistant(
    payload: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 12: AI Governance Assistant

    Ask any election law question in natural language.
    Returns answer with legal citations, relevant judgments, and confidence score.

    Example questions:
    - "Can I contest if a criminal case is pending against me?"
    - "Do I need to disclose my spouse's assets in Form 26?"
    - "What is the election expenditure limit for a Lok Sabha constituency?"
    - "Can the party publish an advertisement after the MCC is in effect?"
    """
    engine = get_rag_engine()

    result = await engine.answer(
        query=payload.query,
        context=payload.context,
        session_id=payload.session_id,
    )

    # Log query for analytics and feedback
    log = AIQueryLog(
        user_id=current_user.id,
        query=payload.query,
        response=result["answer"],
        legal_basis=result["legal_basis"],
        confidence_score=result["confidence_score"],
        relevant_judgments=result["relevant_judgments"],
        model_used=settings.LLM_MODEL,
        latency_ms=result.get("latency_ms"),
        session_id=payload.session_id,
    )
    db.add(log)

    return AIQueryResponse(
        query=result["query"],
        answer=result["answer"],
        legal_basis=result["legal_basis"],
        relevant_judgments=result["relevant_judgments"],
        recommended_action=result.get("recommended_action"),
        confidence_score=result["confidence_score"],
        sources=result["sources"],
    )


@router.post("/feedback/{query_log_id}")
async def submit_feedback(
    query_log_id: str,
    was_helpful: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit feedback on an AI response."""
    from sqlalchemy import select, update
    import uuid
    await db.execute(
        update(AIQueryLog)
        .where(AIQueryLog.id == uuid.UUID(query_log_id), AIQueryLog.user_id == current_user.id)
        .values(was_helpful=was_helpful)
    )
    return {"message": "Feedback recorded. Thank you."}
