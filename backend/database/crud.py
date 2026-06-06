from sqlalchemy.orm import Session
from .db import AnalysisRecord
from typing import List, Optional
import json


def save_analysis(
    db: Session,
    analysis_id: str,
    session_token: str,
    target_role: str,
    candidate_name: str,
    overall_score: int,
    full_result: dict,
) -> AnalysisRecord:
    """Persist a completed analysis result to the database."""
    record = AnalysisRecord(
        id=analysis_id,
        session_token=session_token,
        target_role=target_role,
        candidate_name=candidate_name,
        overall_score=overall_score,
        full_result_json=json.dumps(full_result),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_analysis_by_id(db: Session, analysis_id: str) -> Optional[AnalysisRecord]:
    """Retrieve a single analysis by its UUID."""
    return db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()


def get_analyses_by_session(
    db: Session, session_token: str, limit: int = 20
) -> List[AnalysisRecord]:
    """Retrieve all analyses for a given session token, newest first."""
    return (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.session_token == session_token)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def delete_analysis(db: Session, analysis_id: str) -> bool:
    """Delete an analysis record. Returns True if deleted, False if not found."""
    record = get_analysis_by_id(db, analysis_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True
