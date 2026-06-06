import uuid
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.crud import save_analysis, get_analysis_by_id, get_analyses_by_session
from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.gemini_service import analyze_resume_with_gemini
from backend.services.score_calculator import enrich_analysis_result, calculate_priority_order
from backend.utils.validators import validate_pdf_upload, sanitize_text
from backend.models.schemas import AnalysisResponse, AnalysisHistoryItem, ErrorResponse

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    request: Request,
    job_role: str = Form(..., min_length=2, max_length=100, description="Target job role"),
    file: Optional[UploadFile] = File(None, description="Resume PDF file (max 10MB)"),
    resume_text: Optional[str] = Form(None, description="Resume text (paste fallback)"),
    db: Session = Depends(get_db),
):
    """
    Core endpoint: accepts a resume PDF OR pasted text + job role.

    Supports two input modes:
    - PDF upload: file is validated and parsed with PyMuPDF
    - Text paste: resume_text is sanitized directly (fallback for scanned PDFs)

    Flow:
    1. Get resume text from PDF or paste input
    2. Send to Gemini 1.5 Pro for analysis
    3. Enrich and validate the result
    4. Persist to SQLite
    5. Return structured JSON response
    """
    # Step 1 — Get resume text from either PDF or paste
    if file and file.filename:
        # PDF mode — validate and extract
        pdf_bytes = await validate_pdf_upload(file)
        extracted_text = extract_text_from_pdf(pdf_bytes)
    elif resume_text and resume_text.strip():
        # Paste mode — sanitize directly
        extracted_text = sanitize_text(resume_text)
        if len(extracted_text) < 50:
            raise HTTPException(
                status_code=422,
                detail="Pasted resume text is too short. Please paste the full resume content.",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file or paste your resume text.",
        )

    # Step 2 — Run AI analysis
    raw_result = analyze_resume_with_gemini(extracted_text, job_role)

    # Step 4 — Enrich result with computed fields
    enriched = enrich_analysis_result(raw_result, job_role)

    # Sort missing skills by priority
    if "skills_analysis" in enriched and "missing_skills" in enriched["skills_analysis"]:
        enriched["skills_analysis"]["missing_skills"] = calculate_priority_order(
            enriched["skills_analysis"]["missing_skills"]
        )

    # Step 5 — Generate analysis ID and timestamp
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"

    enriched["analysis_id"] = analysis_id
    enriched["created_at"] = created_at

    # Step 6 — Get or create session token from cookie
    session_token = request.cookies.get("session_token", str(uuid.uuid4()))

    # Step 7 — Persist to database
    candidate_name = enriched.get("candidate", {}).get("name", "Anonymous")
    overall_score = enriched.get("job_fit_score", {}).get("overall", 0)

    save_analysis(
        db=db,
        analysis_id=analysis_id,
        session_token=session_token,
        target_role=job_role,
        candidate_name=candidate_name,
        overall_score=overall_score,
        full_result=enriched,
    )

    return enriched


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve a previously completed analysis by its UUID."""
    record = get_analysis_by_id(db, analysis_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return json.loads(record.full_result_json)


@router.get("/history", response_model=list[AnalysisHistoryItem])
def get_history(request: Request, db: Session = Depends(get_db)):
    """Return analysis history for the current session."""
    session_token = request.cookies.get("session_token", "")
    if not session_token:
        return []
    records = get_analyses_by_session(db, session_token)
    return [
        AnalysisHistoryItem(
            analysis_id=r.id,
            target_role=r.target_role,
            overall_score=r.overall_score,
            created_at=r.created_at.isoformat() + "Z",
        )
        for r in records
    ]
