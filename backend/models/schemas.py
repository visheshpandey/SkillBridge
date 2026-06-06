from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    job_role: str = Field(..., min_length=2, max_length=100, description="Target job role to analyze against")


# ---------------------------------------------------------------------------
# Nested Response Schemas
# ---------------------------------------------------------------------------

class CandidateInfo(BaseModel):
    name: str
    experience_years: int
    seniority_level: str  # Junior / Mid-Level / Senior


class ScoreBreakdown(BaseModel):
    technical_skills: int = Field(..., ge=0, le=100)
    experience_relevance: int = Field(..., ge=0, le=100)
    education_alignment: int = Field(..., ge=0, le=100)
    soft_skills: int = Field(..., ge=0, le=100)


class JobFitScore(BaseModel):
    overall: int = Field(..., ge=0, le=100)
    confidence: str  # high / medium / low
    breakdown: ScoreBreakdown


class MatchedSkill(BaseModel):
    skill: str
    proficiency: str       # Beginner / Intermediate / Advanced
    evidence: str          # How it was identified in the resume


class MissingSkill(BaseModel):
    skill: str
    priority: str          # Critical / High / Medium / Low
    hiring_impact: str     # Human-readable impact description
    estimated_weeks: int   # Time to learn this skill


class SkillsAnalysis(BaseModel):
    matched_skills: List[MatchedSkill]
    missing_skills: List[MissingSkill]


class CareerReadiness(BaseModel):
    current_readiness_percent: int = Field(..., ge=0, le=100)
    estimated_weeks_to_ready: int
    predicted_ready_date: str
    bottleneck_skill: str


class LearningResource(BaseModel):
    type: str    # course / documentation / project / book
    title: str
    url: str
    free: bool


class RoadmapPhase(BaseModel):
    phase: int
    title: str
    duration_weeks: int
    skills: List[str]
    resources: List[LearningResource]


class InterviewQuestion(BaseModel):
    question: str
    type: str         # Technical / Behavioral / Situational
    difficulty: str   # Easy / Medium / Hard
    danger_zone: bool
    topic: str


# ---------------------------------------------------------------------------
# Primary API Response Schema
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    analysis_id: str
    created_at: str
    candidate: CandidateInfo
    target_role: str
    job_fit_score: JobFitScore
    skills_analysis: SkillsAnalysis
    career_readiness: CareerReadiness
    learning_roadmap: List[RoadmapPhase]
    interview_questions: List[InterviewQuestion]
    ai_suggestions: List[str]
    strengths: List[str]


# ---------------------------------------------------------------------------
# History & Error Schemas
# ---------------------------------------------------------------------------

class AnalysisHistoryItem(BaseModel):
    analysis_id: str
    target_role: str
    overall_score: int
    created_at: str

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
