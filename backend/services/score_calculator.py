from datetime import datetime, timedelta
from typing import Any


def enrich_analysis_result(raw_result: dict, job_role: str) -> dict:
    """
    Post-process the raw Gemini response to add computed fields,
    validate score ranges, and ensure all required fields are present.

    Args:
        raw_result: Parsed JSON dict from Gemini.
        job_role: Target job role string.

    Returns:
        Enriched and validated result dict.
    """
    # Clamp all score values to valid 0-100 range
    _clamp_scores(raw_result)

    # Compute career readiness predicted date if missing or invalid
    _compute_ready_date(raw_result)

    # Ensure all array fields exist and are non-empty
    _ensure_required_arrays(raw_result)

    # Add job role to result
    raw_result["target_role"] = job_role

    return raw_result


def _clamp_scores(result: dict) -> None:
    """Ensure all score fields are integers within 0-100."""
    try:
        fit = result.get("job_fit_score", {})
        fit["overall"] = _clamp(fit.get("overall", 0))

        breakdown = fit.get("breakdown", {})
        for key in ["technical_skills", "experience_relevance", "education_alignment", "soft_skills"]:
            breakdown[key] = _clamp(breakdown.get(key, 0))

        readiness = result.get("career_readiness", {})
        readiness["current_readiness_percent"] = _clamp(
            readiness.get("current_readiness_percent", 0)
        )
    except Exception:
        pass  # Never crash on enrichment — Gemini result is best-effort


def _compute_ready_date(result: dict) -> None:
    """
    Calculate the predicted ready date from estimated_weeks_to_ready.
    Overwrites whatever Gemini returned to ensure accuracy.
    """
    try:
        readiness = result.get("career_readiness", {})
        weeks = int(readiness.get("estimated_weeks_to_ready", 0))
        ready_date = datetime.utcnow() + timedelta(weeks=weeks)
        readiness["predicted_ready_date"] = ready_date.strftime("%Y-%m-%d")
    except Exception:
        pass


def _ensure_required_arrays(result: dict) -> None:
    """Guarantee that all list fields exist and have at least one item."""
    defaults: dict[str, Any] = {
        "ai_suggestions": ["Review the analysis and focus on the top missing skills."],
        "strengths": ["Analysis complete — review matched skills above."],
        "interview_questions": [],
        "learning_roadmap": [],
    }
    for field, default in defaults.items():
        if not result.get(field):
            result[field] = default

    # Ensure skills_analysis structure exists
    if "skills_analysis" not in result:
        result["skills_analysis"] = {"matched_skills": [], "missing_skills": []}


def _clamp(value: Any, min_val: int = 0, max_val: int = 100) -> int:
    """Clamp a value to integer within [min_val, max_val]."""
    try:
        return max(min_val, min(max_val, int(value)))
    except (TypeError, ValueError):
        return 0


def calculate_priority_order(missing_skills: list) -> list:
    """
    Sort missing skills by priority for display ordering.
    Critical > High > Medium > Low
    """
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    return sorted(
        missing_skills,
        key=lambda s: priority_order.get(s.get("priority", "Low"), 3),
    )
