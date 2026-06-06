# SkillBridge AI — Tech Stack Deep Dive

Every technology used in this project, why we chose it, and exactly how it's used.

---

## Backend

### FastAPI `0.111.0`
**What it is:** A modern Python web framework for building APIs.

**Why we chose it:**
- Async-first design — handles multiple simultaneous uploads without blocking
- Automatic OpenAPI/Swagger docs generated at `/docs` with zero extra work
- Native Pydantic integration for request/response validation
- Significantly faster than Flask for I/O-bound tasks (file uploads, AI API calls)

**How we use it:**
- Single `app` instance in `backend/main.py`
- One router: `POST /api/analyze` — the core endpoint that orchestrates the entire analysis pipeline
- Mounts frontend static files (`/static`, `/js`) so one server handles everything
- Dependency injection for database sessions (`Depends(get_db)`)

```python
app = FastAPI(title="SkillBridge AI", version="1.0.0")
app.include_router(analyze_router)
app.mount("/static", StaticFiles(directory="frontend/css"))
```

---

### Uvicorn `0.30.1`
**What it is:** ASGI server that runs the FastAPI application.

**Why we chose it:**
- Production-grade performance
- `--reload` flag watches for file changes during development
- Handles concurrent connections efficiently with async I/O

**How we use it:**
```bash
uvicorn backend.main:app --reload --port 8000
```

---

### Pydantic `2.7.4`
**What it is:** Data validation library using Python type hints.

**Why we chose it:**
- FastAPI uses it natively for request/response schemas
- Automatic validation — wrong types are rejected before hitting business logic
- Clean schema definitions that double as documentation

**How we use it:**
Every API request and response is defined as a Pydantic model in `backend/models/schemas.py`:

```python
class JobFitScore(BaseModel):
    overall: int = Field(..., ge=0, le=100)
    confidence: str
    breakdown: ScoreBreakdown

class AnalysisResponse(BaseModel):
    analysis_id: str
    candidate: CandidateInfo
    job_fit_score: JobFitScore
    skills_analysis: SkillsAnalysis
    # ...
```

---

### SQLAlchemy `2.0.30`
**What it is:** Python ORM (Object Relational Mapper) for database operations.

**Why we chose it:**
- Abstracts SQL — we work with Python objects, not raw queries
- Supports SQLite for development and PostgreSQL for production with the same code
- Session management integrates cleanly with FastAPI dependency injection

**How we use it:**
`backend/database/db.py` defines the `AnalysisRecord` table model:

```python
class AnalysisRecord(Base):
    __tablename__ = "analyses"
    id = Column(String, primary_key=True)
    session_token = Column(String, index=True)
    target_role = Column(String)
    overall_score = Column(Integer)
    full_result_json = Column(Text)   # entire JSON response cached here
    created_at = Column(DateTime, default=datetime.utcnow)
```

`backend/database/crud.py` exposes clean functions: `save_analysis()`, `get_analysis_by_id()`, `get_analyses_by_session()`.

---

### SQLite (via SQLAlchemy)
**What it is:** Serverless, file-based relational database.

**Why we chose it:**
- Zero configuration — no separate database server to run
- Single `.db` file, portable and easy to inspect
- Sufficient for MVP and hackathon scale
- SQLAlchemy ORM makes migrating to PostgreSQL later a one-line config change

**How we use it:**
```python
DATABASE_URL = "sqlite:///./skillbridge.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

The `check_same_thread: False` flag is required for SQLite to work with FastAPI's async threading model.

---

### python-multipart `0.0.9`
**What it is:** Parses `multipart/form-data` requests (file uploads).

**Why we need it:**
FastAPI requires this to handle `UploadFile` — without it, file uploads fail silently.

**How we use it:**
Installed as a dependency. FastAPI uses it automatically when a route declares `file: UploadFile = File(...)`.

---

### python-dotenv `1.0.1`
**What it is:** Loads environment variables from a `.env` file.

**Why we use it:**
Keeps secrets (API keys, database URLs) out of source code. Each service calls `load_dotenv()` at startup.

```python
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

---

## AI & Document Processing

### Google Generative AI SDK `0.7.2` — Gemini 2.5 Flash
**What it is:** Official Python client for Google's Gemini AI models.

**Why Gemini 2.5 Flash specifically:**
- **Multimodal** — processes both text and images in a single API call
- **Structured JSON output mode** — set `response_mime_type="application/json"` and Gemini guarantees valid JSON back, no parsing hacks needed
- **Fast** — "Flash" variant optimized for speed over maximum reasoning depth
- **Free tier** — higher rate limits than Pro, suitable for demos and hackathons
- **Vision capability** — reads text from images, enabling OCR on scanned PDFs

**How we use it — two distinct calls:**

**Call 1: Vision OCR** (scanned PDF fallback in `pdf_parser.py`)
```python
model = genai.GenerativeModel("gemini-2.5-flash")
parts = [ocr_instruction_text] + [page_image_part, ...]
response = model.generate_content(parts)
extracted_text = response.text
```

**Call 2: Career Analysis** (main analysis in `gemini_service.py`)
```python
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        temperature=0.3,
        response_mime_type="application/json",
    ),
)
response = model.generate_content(prompt_with_resume_and_schema)
result = json.loads(response.text)
```

**Prompt engineering:**
- System prompt establishes the model as an expert recruiter/career coach
- User prompt includes the full resume text, target role, and the exact JSON schema Gemini must produce
- Temperature 0.3 — low randomness for reproducible scores, slight creativity for suggestions
- Schema included in prompt with field descriptions ensures consistent output structure

---

### PyMuPDF (fitz) `1.24.5`
**What it is:** Python binding for the MuPDF library — industry-leading PDF renderer and parser.

**Why we chose it:**
- Fastest Python PDF text extractor available
- Handles complex multi-column layouts and preserves reading order
- Can render PDF pages as images at any resolution (essential for OCR fallback)
- Pure Python install — no system dependencies on most platforms

**How we use it — two modes:**

**Mode 1: Text extraction** (text-based PDFs)
```python
doc = fitz.open(stream=pdf_bytes, filetype="pdf")
for page in doc:
    text = page.get_text("text")  # preserves reading order
```

**Mode 2: Page rendering** (scanned PDFs)
```python
mat = fitz.Matrix(2.0, 2.0)   # 2x resolution for better OCR
pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
png_bytes = pix.tobytes("png")  # → sent to Gemini Vision
```

The two-mode strategy means the same upload endpoint handles all PDF types automatically.

---

### aiofiles `23.2.1`
**What it is:** Async file I/O library for Python.

**Why we include it:**
FastAPI's `StaticFiles` mount requires it for serving static files asynchronously.

---

### Jinja2 `3.1.4`
**What it is:** Python templating engine.

**Why we include it:**
FastAPI's `StaticFiles` and `FileResponse` depend on it internally. Included as an explicit dependency for stability.

---

## Frontend

### HTML5 / CSS3 / Vanilla JavaScript
**Why no framework:**
- Zero build step — no webpack, no npm build process, no compilation
- FastAPI serves the files directly as static assets
- Judges can inspect the code without any tooling
- Loads instantly — no framework bundle overhead

### Design System — Dark Glassmorphism
Inspired by the SkillSync AI reference design:

| Token | Value | Usage |
|---|---|---|
| `--bg` | `#0F1020` | Page background |
| `--mauve` | `#faa6ff` | Primary accent, scores, highlights |
| `--lilac` | `#7353ba` | Secondary accent, gradients |
| `--text` | `#ebdfe7` | Body text |
| `--text-muted` | `#d2c2cf` | Secondary text |
| `--border` | `rgba(255,255,255,0.1)` | Card borders |

**Glass cards:**
```css
.glass-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

**Typography:**
- `Plus Jakarta Sans` — display headings
- `Hanken Grotesk` — body text
- `JetBrains Mono` — labels, badges, code-style elements

### Key JavaScript Patterns

**upload.js**
- FileReader API for client-side PDF validation before upload
- FormData API for multipart form submission
- Fetch API for the `/api/analyze` POST call
- Animated progress overlay with step transitions during analysis

**dashboard.js**
- Reads result from `sessionStorage` (set by upload.js after successful response)
- Animates SVG score donut via `strokeDashoffset` transition
- Animates progress bars via CSS width transitions with `setTimeout` delays
- Renders all sections by building HTML strings and setting `innerHTML`
- Direct URL access supported via `?id=<analysis_id>` query param

---

## Development Tooling

### Virtual Environment (venv)
Standard Python virtual environment isolates project dependencies from the system Python installation.

```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # macOS/Linux
```

### requirements.txt
Pinned exact versions for every dependency. Ensures identical installs across all machines.

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
pymupdf==1.24.5
google-generativeai==0.7.2
sqlalchemy==2.0.30
pydantic==2.7.4
python-dotenv==1.0.1
python-multipart==0.0.9
aiofiles==23.2.1
jinja2==3.1.4
pydantic-settings==2.3.1
```

### .env / .env.example
`.env.example` is committed to git as a template. The actual `.env` file is gitignored — secrets never enter version control.

---

## Architecture Decisions

| Decision | Alternative Considered | Why We Chose This |
|---|---|---|
| Vanilla JS frontend | React / Vue | Zero build step, FastAPI serves directly, simpler for judges to review |
| SQLite | PostgreSQL | Zero config, portable, sufficient for MVP; SQLAlchemy makes switching trivial |
| Gemini 2.5 Flash | GPT-4o, Claude | Multimodal (vision OCR), JSON mode, higher free tier limits, Google ecosystem |
| Single FastAPI server | Separate frontend server | One port, one process, simpler deployment and local setup |
| PyMuPDF | pdfplumber, pdfminer | Fastest extraction, can also render pages as images for OCR |
| Session tokens | User accounts | No PII collected, no auth complexity, faster to demo |
| In-memory PDF processing | Save to disk | More secure — PDF bytes never written to filesystem |
