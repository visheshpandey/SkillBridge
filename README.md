# SkillBridge AI

> **AI-powered career intelligence platform** — transform your resume into a personalized career roadmap in under 30 seconds.

Built with **FastAPI** · **Google Gemini 2.5 Flash** · **PyMuPDF** · **SQLite** · **Vanilla JS**

---

## Problem Statement

The global talent market suffers from a fundamental information asymmetry: job seekers invest months applying to roles without understanding *why* they are rejected, while recruiters spend up to 40% of their time screening candidates who lack critical skills.

Traditional resume checkers offer surface-level keyword matching — they don't explain gaps, don't rank skill priority, and don't provide actionable learning paths.

> **Candidates are flying blind. They know they weren't hired — they don't know what to fix or how long it will take.**

---

## Solution

SkillBridge AI transforms a static resume PDF into a living career intelligence report. Upload your resume, pick a target role, and in under 30 seconds get:

| Feature | Description |
|---|---|
| 🎯 **Job Fit Score** | 0–100 score with breakdown by technical skills, experience, education, and soft skills |
| 🔍 **Skill Gap Analysis** | Missing skills ranked by hiring impact — Critical / High / Medium / Low |
| 🗺️ **Learning Roadmap** | Phased learning plan with curated resources and time-to-proficiency per skill |
| 🎤 **Interview Questions** | 10+ AI-generated questions tailored to your profile with danger zone flags |
| 📈 **Career Readiness ETA** | Exact predicted date when you'll be hire-ready |
| 💡 **AI Suggestions** | Personalized tips to strengthen your resume and increase interview chances |

SkillBridge AI is not a resume formatter — it is a career co-pilot.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | HTML5 / CSS3 / Vanilla JS | Zero build step, FastAPI serves directly, instant load |
| Backend | FastAPI (Python 3.11+) | Async-first, auto OpenAPI docs, production-grade |
| AI Engine | Google Gemini 2.5 Flash | Multimodal vision + structured JSON output mode |
| PDF Parsing | PyMuPDF (fitz) | Fastest extractor, can render pages as images for OCR |
| Database | SQLite via SQLAlchemy ORM | Zero config, portable, easy migration path to PostgreSQL |

---

## How It Works

```
User uploads PDF + picks role
        ↓
FastAPI validates the file (MIME type + magic bytes)
        ↓
PyMuPDF extracts text
  → If scanned PDF: render pages as images → Gemini Vision OCR
        ↓
Gemini 2.5 Flash analyzes resume against role
  → Returns structured JSON: scores, gaps, roadmap, questions
        ↓
Result saved to SQLite, returned to browser
        ↓
Dashboard renders animated score, skill tags, roadmap, questions
```

---

## Project Structure

```
skillbridge-ai/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── routers/analyze.py       # POST /api/analyze endpoint
│   ├── services/
│   │   ├── pdf_parser.py        # PyMuPDF + Gemini Vision OCR fallback
│   │   ├── gemini_service.py    # Gemini 2.5 Flash client + prompts
│   │   └── score_calculator.py  # Result enrichment and validation
│   ├── models/schemas.py        # Pydantic request/response schemas
│   ├── database/                # SQLAlchemy models + CRUD
│   └── utils/validators.py      # PDF validation + text sanitization
├── frontend/
│   ├── index.html               # Landing page
│   ├── upload.html              # Resume upload page
│   ├── dashboard.html           # Analysis results dashboard
│   ├── css/styles.css           # Dark glassmorphism design system
│   └── js/                      # Upload logic + dashboard rendering
├── docs/
│   ├── PROJECT_OVERVIEW.md      # Full workflow and AI integration details
│   └── TECH_STACK.md            # Deep dive into every technology used
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup & Running Locally

### Prerequisites
- Python 3.11+
- Google Gemini API key — free at [aistudio.google.com](https://aistudio.google.com/app/apikey)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/visheshpandey/SkillBridge.git
cd SkillBridge/skillbridge-ai

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Open .env and add your key:
# GEMINI_API_KEY=your_gemini_api_key_here

# 5. Start the server
uvicorn backend.main:app --reload --port 8000
```

---

## Demo Instructions

Once the server is running at `http://localhost:8000`:

**Step 1 — Open the app**
```
http://localhost:8000
```

**Step 2 — Go to the upload page**
```
http://localhost:8000/upload
```

**Step 3 — Upload a resume**
- Drag and drop any resume PDF onto the upload zone
- Both text-based PDFs (Word/Google Docs exports) and scanned PDFs are supported
- Max file size: 10MB

**Step 4 — Select a target role**
- Pick from the dropdown (Full Stack Developer, Data Scientist, Product Manager, etc.)
- Or type a custom role in the text field

**Step 5 — Click "Analyze My Readiness"**
- The analysis takes 10–25 seconds
- Progress steps animate while Gemini processes the resume

**Step 6 — View your results**
- Automatically redirected to the dashboard at `http://localhost:8000/dashboard`
- Scroll through: Job Fit Score → Skill Gaps → Career Readiness → Roadmap → Interview Questions → AI Suggestions

**API Explorer**
```
http://localhost:8000/docs
```
Interactive Swagger UI to test the API directly.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | **Required.** Google Gemini API key |
| `DATABASE_URL` | `sqlite:///./skillbridge.db` | Database connection URL |
| `MAX_FILE_SIZE` | `10485760` | Max upload size in bytes (10MB) |
| `ALLOWED_ORIGINS` | `http://localhost:8000` | CORS allowed origins (comma-separated) |

---

## Documentation

- **[Project Overview & AI Integration →](docs/PROJECT_OVERVIEW.md)**
- **[Tech Stack Deep Dive →](docs/TECH_STACK.md)**

---

## License

MIT — built for the 2026 Hackathon.
