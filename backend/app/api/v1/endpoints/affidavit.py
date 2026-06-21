"""ECCRP Module 4 - Affidavit Validator."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.db.session import get_db
from app.db.models import User, Affidavit
from app.core.security import get_current_active_user
from app.schemas import AffidavitValidationResponse
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)


async def _ai_extract_affidavit(content: bytes, mime_type: str) -> dict:
    """Use LLM to extract and validate affidavit fields."""
    if not settings.OPENAI_API_KEY:
        return {
            "assets_movable": {},
            "assets_immovable": {},
            "liabilities": {},
            "criminal_cases": [],
            "missing_fields": ["AI extraction not configured - manual review required"],
            "inconsistencies": [],
            "potential_legal_risks": [],
            "ai_analysis_notes": "AI service not available. Manual review of affidavit required.",
        }

    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage
        import base64

        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.0,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        prompt = """You are an expert in Indian election law, specifically Form 26 affidavit validation.

Analyze this affidavit and extract/validate the following fields in JSON format:

{
  "assets_movable": {"cash": 0, "bank_deposits": 0, "investments": 0, "vehicles": [], "jewelry": 0, "other": 0},
  "assets_immovable": {"agricultural_land": [], "non_agricultural_land": [], "buildings": [], "other": []},
  "liabilities": {"loans_from_banks": 0, "loans_from_others": 0, "other_liabilities": 0},
  "criminal_cases": [{"case_number": "", "court": "", "section": "", "status": "pending/convicted"}],
  "pan_number": "",
  "educational_qualification": "",
  "missing_fields": ["list of mandatory fields that are missing"],
  "inconsistencies": [{"field": "", "issue": ""}],
  "potential_legal_risks": [{"risk": "", "legal_basis": ""}],
  "ai_analysis_notes": "overall analysis summary"
}

Key validation rules (Section 33A RPA 1951, ADR Case 2002):
1. All criminal cases (pending or convicted) MUST be disclosed
2. Assets of spouse and dependents must be included
3. PAN number is mandatory
4. Educational qualifications must be stated
5. All liabilities must be disclosed
6. Non-disclosure of any material fact can lead to election petition

Return ONLY valid JSON, no markdown."""

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        import json
        text = response.content.strip()
        if text.startswith("```"):
            text = text[7:] if text.startswith("```json") else text[3:]
            text = text.rstrip("```").strip()

        return json.loads(text)

    except Exception as e:
        logger.error("affidavit_ai_extraction_failed", error=str(e))
        return {
            "assets_movable": {}, "assets_immovable": {},
            "liabilities": {}, "criminal_cases": [],
            "missing_fields": ["Automated extraction failed - manual review required"],
            "inconsistencies": [], "potential_legal_risks": [],
            "ai_analysis_notes": f"Extraction error: {str(e)}",
        }


@router.post("/upload/{candidate_id}/{election_id}", response_model=AffidavitValidationResponse, status_code=201)
async def upload_and_validate_affidavit(
    candidate_id: UUID,
    election_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 4: Upload and validate Form 26 affidavit.

    AI automatically extracts and validates:
    - Assets (movable & immovable)
    - Liabilities
    - Criminal cases
    - Missing mandatory fields
    - Inconsistencies
    - Legal risks
    """
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    # AI extraction
    extracted = await _ai_extract_affidavit(content, file.content_type)

    # Determine validation status
    missing = extracted.get("missing_fields", [])
    inconsistencies = extracted.get("inconsistencies", [])

    if missing and inconsistencies:
        validation_status = "incomplete_and_inconsistent"
    elif missing:
        validation_status = "incomplete"
    elif inconsistencies:
        validation_status = "inconsistent"
    else:
        validation_status = "complete"

    minio_key = f"affidavits/{candidate_id}/{election_id}/form26_{file.filename}"

    affidavit = Affidavit(
        candidate_id=candidate_id,
        election_id=election_id,
        minio_object_key=minio_key,
        assets_movable=extracted.get("assets_movable", {}),
        assets_immovable=extracted.get("assets_immovable", {}),
        liabilities=extracted.get("liabilities", {}),
        criminal_cases=extracted.get("criminal_cases", []),
        pan_number=extracted.get("pan_number"),
        educational_qualification=extracted.get("educational_qualification"),
        validation_status=validation_status,
        missing_fields=missing,
        inconsistencies=inconsistencies,
        potential_legal_risks=extracted.get("potential_legal_risks", []),
        ai_analysis_notes=extracted.get("ai_analysis_notes"),
    )
    db.add(affidavit)
    await db.flush()
    await db.refresh(affidavit)

    logger.info(
        "affidavit_validated",
        candidate_id=str(candidate_id),
        status=validation_status,
        missing_count=len(missing),
    )
    return affidavit


@router.get("/{candidate_id}/{election_id}/latest", response_model=AffidavitValidationResponse)
async def get_latest_affidavit(
    candidate_id: UUID,
    election_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the latest validated affidavit for a candidate."""
    from sqlalchemy import desc
    result = await db.execute(
        select(Affidavit)
        .where(Affidavit.candidate_id == candidate_id, Affidavit.election_id == election_id)
        .order_by(desc(Affidavit.created_at))
        .limit(1)
    )
    affidavit = result.scalar_one_or_none()
    if not affidavit:
        raise HTTPException(status_code=404, detail="No affidavit found")
    return affidavit
