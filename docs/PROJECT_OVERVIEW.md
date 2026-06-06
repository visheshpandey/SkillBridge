# SkillBridge AI — Project Overview

## What Is SkillBridge AI?

SkillBridge AI is an AI-powered career intelligence platform. A user uploads their resume PDF and selects a target job role. In under 30 seconds, the platform delivers a complete career intelligence report — job fit score, skill gap analysis, learning roadmap, interview questions, and career readiness prediction.

The core insight: candidates are rejected without knowing *why*. SkillBridge AI tells them exactly what to fix, in what order, and how long it will take.

---

## The Problem We Solve

| Problem | SkillBridge AI Solution |
|---|---|
| Candidates don't know why they're rejected | Quantified Job Fit Score with detailed breakdown |
| No visibility into which skills are missing | Prioritized Skill Gap Report (Critical / High / Medium / Low) |
| No guidance on what to learn next | Phased Learning Roadmap with resources + time estimates |
| Unprepared for interviews | AI-generated interview questions with danger zone flags |
| No timeline to become hire-ready | Career Readiness ETA with predicted date |

---

## Full Data Flow

```
┌─────────────────────────────────────────────────────┐
│                   USER BROWSER                      │
│                                                     │
│  [Landing Page]                                     │
│       ↓                                             │
│  [Upload Page] — drag/drop PDF + select role        │
│       ↓  HTTP POST /api/analyze                     │
│       ↓  multipart/form-data                        │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND                    │
│                                                     │
│  1. validators.py                                   │
│     ├── Check file extension (.pdf)                 │
│     ├── Check MIME type (application/pdf)           │
│     ├── Check file size (max 10MB)                  │
│     └── Check magic bytes (%PDF)                    │
│                                                     │
│  2. pdf_parser.py                                   │
│     ├── Try PyMuPDF text extraction (fast path)     │
│     │   └── If text found → sanitize → use it       │
│     └── If no text (scanned PDF):                   │
│         ├── Render pages as PNG at 2x resolution    │
│         └── Send images to Gemini Vision OCR        │
│             └── Gemini reads image → returns text   │
│                                                     │
│  3. gemini_service.py                               │
│     ├── Build structured prompt with:               │
│     │   ├── System instruction (expert recruiter)   │
│     │   ├── Resume text                             │
│     │   ├── Target job role                         │
│     │   └── Exact JSON schema to fill               │
│     ├── Call Gemini 2.5 Flash (JSON mode)           │
│     └── Parse + return structured dict              │
│                                                     │
│  4. score_calculator.py                             │
│     ├── Clamp all scores to 0–100                   │
│     ├── Compute predicted ready date from weeks     │
│     ├── Sort missing skills by priority             │
│     └── Ensure all required fields exist            │
│                                                     │
│  5. database/crud.py                                │
│     └── Save full result to SQLite                  │
│         (linked to session token cookie)            │
│                                                     │
│  6. Return JSON response                            │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│                   USER BROWSER                      │
│                                                     │
│  Result saved to sessionStorage                     │
│  Redirect to /dashboard                             │
│                                                     │
│  [Dashboard Page]                                   │
│  dashboard.js reads sessionStorage and renders:     │
│  ├── Animated score donut (SVG)                     │
│  ├── Score breakdown progress bars                  │
│  ├── Matched skills tags                            │
│  ├── Missing skills with priority pills             │
│  ├── Career readiness stats                         │
│  ├── Roadmap milestone track                        │
│  ├── Interview question cards                       │
│  └── AI suggestions + strengths                     │
└─────────────────────────────────────────────────────┘
```

---

## AI Integration — How We Use Gemini 2.5 Flash

### Why Gemini 2.5 Flash

- **Multimodal** — handles both text prompts AND image inputs (used for scanned PDF OCR)
- **Structured JSON output mode** — guarantees parseable responses without hallucinated formatting
- **Fast** — sub-10 second response time on most resumes
- **Free tier** — sufficient for hackathon and demo use

### Two Ways We Call Gemini

**Call 1 — Vision OCR (scanned PDFs only)**

When PyMuPDF finds no text in a PDF, we render each page as a high-resolution PNG and send it to Gemini with this prompt:

```
You are an OCR engine. Extract ALL text visible in these resume page images.
Preserve the structure: name, contact info, work experience, education, skills,
projects, certifications. Output plain text only — no markdown, no commentary.
```

Gemini reads the image and returns the resume as plain text, which then flows into the normal analysis pipeline.

**Call 2 — Career Analysis (all resumes)**

The extracted resume text is sent with a detailed system prompt and a strict JSON schema:

```python
SYSTEM_PROMPT = """
You are an expert technical recruiter and career coach with 15 years of experience.
Analyze the provided resume against the target job role.
You MUST respond with valid JSON only. No markdown, no explanation outside JSON.
"""
```

The user prompt includes the full resume text, the target role, and the exact JSON schema Gemini must fill — including candidate info, job fit score, matched skills, missing skills, career readiness, learning roadmap, interview questions, suggestions, and strengths.

### Prompt Engineering Decisions

| Decision | Rationale |
|---|---|
| Temperature: 0.3 | Low randomness for reproducible, calibrated scores |
| JSON mode enforced | Prevents prose responses that break parsing |
| Schema included in prompt | Guarantees correct field names and types |
| Few-shot score calibration | Instructs Gemini that average developers score 50–65, not 90+ |
| Single API call | Entire analysis in one request — faster and cheaper |

### Security: API Key Never Exposed

The browser never communicates with Gemini directly. All AI calls happen server-side:

```
Browser → FastAPI → Gemini API → FastAPI → Browser
```

The `GEMINI_API_KEY` lives only in the server's `.env` file and is never sent to the frontend.

---

## PDF Handling Strategy

### Text-Based PDFs (Google Docs, Word, Canva exports)

```
PDF bytes → PyMuPDF → extract text per page → sanitize → analyze
```

Fast path — no AI needed for extraction. Takes milliseconds.

### Scanned / Image PDFs (photos, scanner output)

```
PDF bytes → PyMuPDF (no text found) →
render pages as 2x PNG images →
send to Gemini Vision →
Gemini reads images → returns text →
sanitize → analyze
```

This is fully automatic — the user just uploads their PDF and it works either way.

### Text Sanitization

Before any text reaches the AI:
- Null bytes removed
- Excessive whitespace collapsed
- Text capped at 60,000 characters (prevents token overflow)
- Prompt injection patterns neutralized

---

## Feature Breakdown

### Job Fit Score
A 0–100 integer representing how well the resume matches the target role. Broken down into four sub-scores: technical skills, experience relevance, education alignment, and soft skills. Includes a confidence level (high / medium / low).

### Skill Gap Analysis
Two lists:
- **Matched skills** — skills found in the resume with proficiency level and evidence from the resume text
- **Missing skills** — skills required for the role but absent, ranked by hiring impact (Critical / High / Medium / Low) with estimated weeks to learn each one

### Learning Roadmap
A sequenced 2–3 phase learning plan. Each phase has:
- A title (e.g. "Foundation Sprint")
- Duration in weeks
- Specific skills to acquire
- Curated learning resources with free/paid flag

Phases are ordered foundational → advanced so the candidate builds in the right sequence.

### Career Readiness
- Current readiness percentage
- Total estimated weeks to become hire-ready
- Predicted ready date (computed from current date + weeks)
- The single bottleneck skill blocking the most progress

### Interview Questions
10+ questions generated specifically for the candidate's gap profile. Each question has:
- Type: Technical / Behavioral / Situational
- Difficulty: Easy / Medium / Hard
- Topic area
- Danger zone flag (true if the candidate is weakest in this area)

### AI Suggestions & Strengths
3–5 actionable suggestions to improve the resume (e.g. "Add quantified metrics to project descriptions") and 3–5 specific strengths identified from the resume content.

---

## Database Design

A single `analyses` table stores every completed analysis:

| Column | Type | Purpose |
|---|---|---|
| `id` | UUID string | Primary key |
| `session_token` | string | Links to user session (no accounts needed) |
| `target_role` | string | The job role analyzed |
| `candidate_name` | string | Extracted from resume |
| `overall_score` | integer | For history display |
| `full_result_json` | text | Complete JSON response cached |
| `created_at` | datetime | Timestamp |

Session tokens (UUID v4) replace user accounts — no PII collected at MVP stage.

---

## Frontend Architecture

Three pages, zero JavaScript frameworks:

| Page | File | Purpose |
|---|---|---|
| Landing | `index.html` | Product overview, features, CTA |
| Upload | `upload.html` | PDF drag-and-drop, role selection, form submission |
| Dashboard | `dashboard.html` | Full analysis results with animated visualizations |

### Data Flow in the Browser

```
upload.js submits FormData to /api/analyze
       ↓
Response JSON saved to sessionStorage
       ↓
Browser redirects to /dashboard
       ↓
dashboard.js reads sessionStorage
       ↓
Renders all sections by manipulating DOM directly
```

No frameworks, no build step, no bundler. FastAPI serves all HTML/CSS/JS as static files.

### Design System

Dark glassmorphism UI inspired by SkillSync AI:
- Background: `#0F1020` (deep navy)
- Primary accent: `#faa6ff` (mauve/pink)
- Secondary accent: `#7353ba` (deep lilac)
- Fonts: Plus Jakarta Sans (display) + Hanken Grotesk (body) + JetBrains Mono (labels)
- Cards: glassmorphism with `backdrop-filter: blur(20px)`
- Buttons: gradient `#faa6ff → #7353ba` with glow on hover

---

## Security Measures

| Threat | Mitigation |
|---|---|
| Malicious file upload | MIME type + magic bytes (`%PDF`) validation |
| Prompt injection via resume | Text sanitized — null bytes removed, length capped |
| API key exposure | Key stored server-side only, never in frontend code |
| Resource abuse | Rate limiting: 10 analyses per IP per hour |
| Cross-origin attacks | CORS whitelist configured via environment variable |
| PDF storage | PDFs never written to disk — processed in memory only |
