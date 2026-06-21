"""ECCRP Module 3 - Nomination Readiness Engine."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User, NominationReadiness, NominationDocument, DocumentType, Candidate, Election
from app.core.security import get_current_active_user
from app.schemas import NominationReadinessResponse

router = APIRouter()

DOCUMENT_WEIGHTS = {
    DocumentType.FORM_26: ("affidavit_score", 25),
    DocumentType.ELECTORAL_ROLL_PROOF: ("electoral_roll_score", 20),
    DocumentType.ASSETS_DECLARATION: ("assets_score", 15),
    DocumentType.LIABILITIES_DECLARATION: ("liabilities_score", 10),
    DocumentType.CRIMINAL_DISCLOSURE: ("criminal_disclosure_score", 15),
    DocumentType.IDENTITY_PROOF: ("photograph_score", 15),
}


@router.post("/upload/{candidate_id}/{election_id}", status_code=201)
async def upload_nomination_document(
    candidate_id: UUID,
    election_id: UUID,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a nomination document (Form 26, electoral roll proof, etc.)."""
    from app.core.config import settings
    import mimetypes

    # Validate file type
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
    if content_type not in settings.ALLOWED_UPLOAD_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {content_type}")

    # Read file for size check
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    # In production: upload to MinIO
    minio_key = f"nominations/{candidate_id}/{election_id}/{document_type.value}/{file.filename}"

    doc = NominationDocument(
        candidate_id=candidate_id,
        election_id=election_id,
        document_type=document_type,
        document_name=file.filename,
        minio_object_key=minio_key,
        file_size_bytes=len(content),
        mime_type=content_type,
        is_complete=True,
    )
    db.add(doc)
    await db.flush()

    # Recalculate readiness score
    await _recalculate_readiness(db, candidate_id, election_id)

    return {"message": "Document uploaded successfully", "document_id": str(doc.id)}


async def _recalculate_readiness(db: AsyncSession, candidate_id: UUID, election_id: UUID):
    """Recalculate nomination readiness score based on uploaded docs."""
    docs_result = await db.execute(
        select(NominationDocument).where(
            NominationDocument.candidate_id == candidate_id,
            NominationDocument.election_id == election_id,
            NominationDocument.is_active == True,
        )
    )
    docs = docs_result.scalars().all()
    uploaded_types = {d.document_type for d in docs if d.is_complete}

    scores = {
        "form_score": 0.0, "affidavit_score": 0.0, "security_deposit_score": 0.0,
        "electoral_roll_score": 0.0, "photograph_score": 0.0, "pan_score": 0.0,
        "assets_score": 0.0, "liabilities_score": 0.0, "criminal_disclosure_score": 0.0,
    }
    total_possible = 0
    total_earned = 0

    for doc_type, (score_key, weight) in DOCUMENT_WEIGHTS.items():
        total_possible += weight
        if doc_type in uploaded_types:
            scores[score_key] = 100.0
            total_earned += weight

    overall = (total_earned / total_possible * 100) if total_possible else 0

    # Upsert readiness record
    existing = await db.execute(
        select(NominationReadiness).where(
            NominationReadiness.candidate_id == candidate_id,
            NominationReadiness.election_id == election_id,
        )
    )
    readiness = existing.scalar_one_or_none()

    pending = [dt.value for dt in DOCUMENT_WEIGHTS.keys() if dt not in uploaded_types]
    completed = [dt.value for dt in uploaded_types]

    if readiness:
        for k, v in scores.items():
            setattr(readiness, k, v)
        readiness.overall_readiness_score = overall
        readiness.pending_items = [{"item": p} for p in pending]
        readiness.completed_items = [{"item": c} for c in completed]
    else:
        readiness = NominationReadiness(
            candidate_id=candidate_id,
            election_id=election_id,
            overall_readiness_score=overall,
            pending_items=[{"item": p} for p in pending],
            completed_items=[{"item": c} for c in completed],
            **scores,
        )
        db.add(readiness)
    await db.flush()


@router.get("/{candidate_id}/{election_id}", response_model=NominationReadinessResponse)
async def get_nomination_readiness(
    candidate_id: UUID,
    election_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get nomination readiness score and checklist."""
    result = await db.execute(
        select(NominationReadiness).where(
            NominationReadiness.candidate_id == candidate_id,
            NominationReadiness.election_id == election_id,
        )
    )
    readiness = result.scalar_one_or_none()
    if not readiness:
        # Return zero-scored readiness if no documents uploaded yet
        return NominationReadinessResponse(
            candidate_id=candidate_id,
            election_id=election_id,
            overall_readiness_score=0.0,
            form_score=0.0, affidavit_score=0.0, security_deposit_score=0.0,
            electoral_roll_score=0.0, photograph_score=0.0, pan_score=0.0,
            assets_score=0.0, liabilities_score=0.0, criminal_disclosure_score=0.0,
            pending_items=[{"item": dt.value, "description": "Not uploaded"} for dt in DOCUMENT_WEIGHTS],
            completed_items=[],
        )
    return readiness
