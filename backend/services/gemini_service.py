import os
import json
import time
import google.generativeai as genai
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert technical recruiter and career coach with 15 years of experience 
at top-tier technology companies. You specialize in evaluating candidates for software engineering, 
data science, product management, and design roles.

Your task is to analyze a resume against a target job role and produce a comprehensive career 
intelligence report. Be honest, specific, and actionable in your assessment.

CRITICAL: You MUST respond with valid JSON only. No markdown, no explanation, no text outside the JSON object.
"""

USER_PROMPT_TEMPLATE = """
Resume Content:
{resume_text}

Target Role: {job_role}

Analyze this resume against the target role and respond with JSON matching this EXACT schema:

{{
  "candidate": {{
    "name": "string - extract from resume or use Anonymous",
    "experience_years": "integer - total years of professional experience",
    "seniority_level": "string - Junior / Mid-Level / Senior / Lead"
  }},
  "job_fit_score": {{
    "overall": "integer 0-100",
    "confidence": "string - high / medium / low",
    "breakdown": {{
      "technical_skills": "integer 0-100",
      "experience_relevance": "integer 0-100",
      "education_alignment": "integer 0-100",
      "soft_skills": "integer 0-100"
    }}
  }},
  "skills_analysis": {{
    "matched_skills": [
      {{
        "skill": "string",
        "proficiency": "string - Beginner / Intermediate / Advanced",
        "evidence": "string - specific evidence from resume"
      }}
    ],
    "missing_skills": [
      {{
        "skill": "string",
        "priority": "string - Critical / High / Medium / Low",
        "hiring_impact": "string - impact on hiring chances",
        "estimated_weeks": "integer - weeks to learn"
      }}
    ]
  }},
  "career_readiness": {{
    "current_readiness_percent": "integer 0-100",
    "estimated_weeks_to_ready": "integer",
    "predicted_ready_date": "string - YYYY-MM-DD format",
    "bottleneck_skill": "string - the single most critical missing skill"
  }},
  "learning_roadmap": [
    {{
      "phase": "integer starting from 1",
      "title": "string - phase name",
      "duration_weeks": "integer",
      "skills": ["array of skill strings"],
      "resources": [
        {{
          "type": "string - course / documentation / project / book",
          "title": "string",
          "url": "string",
          "free": "boolean"
        }}
      ]
    }}
  ],
  "interview_questions": [
    {{
      "question": "string",
      "type": "string - Technical / Behavioral / Situational",
      "difficulty": "string - Easy / Medium / Hard",
      "danger_zone": "boolean - true if candidate is weak in this area",
      "topic": "string"
    }}
  ],
  "ai_suggestions": ["array of 3-5 specific actionable suggestion strings"],
  "strengths": ["array of 3-5 specific strength strings found in the resume"]
}}

Rules:
- matched_skills: include ALL skills found in the resume relevant to the role (minimum 3)
- missing_skills: include ALL important skills missing from the resume (minimum 3)  
- learning_roadmap: create 2-3 phases sequenced from foundational to advanced
- interview_questions: generate exactly 10 questions mixing all types
- Be specific and reference actual content from the resume
- Scores must be realistic and calibrated (average developer is 50-65, not 90+)
"""


# ---------------------------------------------------------------------------
# Gemini Service
# ---------------------------------------------------------------------------

def analyze_resume_with_gemini(resume_text: str, job_role: str) -> dict:
    """
    Send resume + job role to Gemini 1.5 Pro and return structured analysis.

    Uses retry logic with exponential backoff to handle rate limits gracefully.

    Args:
        resume_text: Cleaned text extracted from the resume PDF.
        job_role: Target job role string (e.g. "Full Stack Developer").

    Returns:
        Parsed dict matching the AnalysisResponse schema.

    Raises:
        HTTPException 502 if Gemini API fails after all retries.
        HTTPException 500 if response cannot be parsed as valid JSON.
    """
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    prompt = USER_PROMPT_TEMPLATE.format(
        resume_text=resume_text,
        job_role=job_role,
    )

    # Retry with exponential backoff (handles rate limits)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            # Parse JSON response
            result = json.loads(raw_text)
            return result

        except json.JSONDecodeError as e:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"AI returned malformed JSON. Please try again. ({str(e)})",
                )

        except Exception as e:
            error_str = str(e).lower()

            # Rate limit — wait and retry
            if "quota" in error_str or "rate" in error_str or "429" in error_str:
                wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                time.sleep(wait_time)
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=429,
                        detail="AI service rate limit reached. Please try again in a moment.",
                    )

            # API key issue
            elif "api_key" in error_str or "401" in error_str or "403" in error_str:
                raise HTTPException(
                    status_code=502,
                    detail="Gemini API key is invalid or missing. Check your .env configuration.",
                )

            else:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=502,
                        detail=f"AI service unavailable. Please try again. ({str(e)})",
                    )
                time.sleep(2 ** attempt)

    raise HTTPException(status_code=502, detail="AI analysis failed after multiple retries.")
