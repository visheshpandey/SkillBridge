# SkillBridge AI

> **AI-powered career intelligence platform** — transform your resume into a personalized career roadmap in under 30 seconds.

Built with **FastAPI** · **Google Gemini 1.5 Pro** · **PyMuPDF** · **SQLite** · **Vanilla JS**

---

## What It Does

SkillBridge AI accepts a resume PDF and a target job role, then delivers a full career intelligence report:

| Feature | Description |
|---|---|
| 🎯 **Job Fit Score** | 0–100 score with breakdown by technical skills, experience, education, and soft skills |
| 🔍 **Skill Gap Analysis** | Missing skills ranked by hiring impact (Critical / High / Medium / Low) |
| 🗺️ **Learning Roadmap** | Phased plan with curated resources and estimated time-to-proficiency |
| 🎤 **Interview Questions** | 10+ AI-generated questions tailored to the candidate's profile with danger zone flags |
| 📈 **Career Readiness ETA** | Predicted date when the candidate will be hire-ready |
| 💡 **AI Suggestions** | Personalized, actionable tips to strengthen the resume |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5 / CSS3 / Vanilla JS (glassmorphism dark UI) |
| Backend | FastAPI (Python 3.11+) with async endpoints |
| AI Engine | Google Gemini 1.5 Pro (structured JSON mode) |
| PDF Parsing | PyMuPDF (fitz) — fast, accurate text extraction |
| Database | SQLite via SQLAlchemy ORM |

---

## Project Structure

```
skillbridge-ai/
├── backend/
│   ├── main.py                  # FastAPI app entry point + static file serving
│   ├── routers/
│   │   └── analyze.py           # POST /api/analyze endpoint
│   ├── services/
│   │   ├── pdf_parser.py        # PyMuPDF text extraction
│   │   ├── gemini_service.py    # Gemini API client + prompt templates
│   │   └── score_calculator.py  # Result enrichment and validation
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── database/
│   │   ├── db.py                # SQLAlchemy setup + AnalysisRecord model
│   │   └── crud.py              # DB read/write operations
│   └── utils/
│       └── validators.py        # PDF validation + text sanitization
├── frontend/
│   ├── index.html               # Landing page
│   ├── upload.html              # Resume upload page
│   ├── dashboard.html           # Analysis results dashboard
│   ├── css/
│   │   └── styles.css           # Dark glassmorphism design system
│   └── js/
│       ├── upload.js            # Drag-and-drop, form validation, submission
│       └── dashboard.js         # Dashboard rendering and animations
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup & Running Locally

### Prerequisites

- Python 3.11+
- A Google Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com/app/apikey)

### 1. Clone the repository

```bash
git clone https://github.com/visheshpandey/SkillBridge.git
cd SkillBridge/skillbridge-ai
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Start the server

```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Open in browser

```
http://localhost:8000
```

The API docs are also available at:

```
http://localhost:8000/docs
```

---

## API Reference

### `POST /api/analyze`

Accepts a resume PDF and job role, returns a full analysis report.

**Request** — `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | PDF file | Resume PDF, max 10MB |
| `job_role` | string | Target job role (e.g. "Full Stack Developer") |

**Response** — `application/json`

```json
{
  "analysis_id": "uuid-v4",
  "created_at": "2026-06-06T10:30:00Z",
  "candidate": { "name": "...", "experience_years": 3, "seniority_level": "Mid-Level" },
  "target_role": "Full Stack Developer",
  "job_fit_score": { "overall": 72, "confidence": "high", "breakdown": { ... } },
  "skills_analysis": { "matched_skills": [...], "missing_skills": [...] },
  "career_readiness": { "current_readiness_percent": 72, "estimated_weeks_to_ready": 14, ... },
  "learning_roadmap": [...],
  "interview_questions": [...],
  "ai_suggestions": [...],
  "strengths": [...]
}
```

### `GET /api/analysis/{analysis_id}`

Retrieve a previously completed analysis by its UUID.

### `GET /health`

Health check endpoint.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | **Required.** Google Gemini API key |
| `DATABASE_URL` | `sqlite:///./skillbridge.db` | SQLAlchemy database URL |
| `MAX_FILE_SIZE` | `10485760` | Max upload size in bytes (10MB) |
| `RATE_LIMIT_PER_HOUR` | `10` | Max analyses per IP per hour |
| `ALLOWED_ORIGINS` | `http://localhost:8000` | CORS allowed origins (comma-separated) |

---

## Security Notes

- Resume PDFs are **never stored to disk** — text is extracted in memory and the bytes are discarded
- Gemini API key is **never exposed to the frontend** — all AI calls happen server-side
- Uploaded files are validated by **MIME type + PDF magic bytes** to prevent disguised uploads
- Resume text is **sanitized** before prompt injection to prevent prompt hijacking

---

## License

MIT — built for the 2026 Hackathon.
