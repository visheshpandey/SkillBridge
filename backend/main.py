import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from backend.database.db import init_db
from backend.routers.analyze import router as analyze_router
from backend.models.schemas import HealthResponse

load_dotenv()

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SkillBridge AI",
    description="AI-powered career intelligence — resume analysis, skill gap detection, and learning roadmaps.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Database Setup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    init_db()


# ---------------------------------------------------------------------------
# API Routers
# ---------------------------------------------------------------------------

app.include_router(analyze_router)

# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Simple health check endpoint for monitoring."""
    return HealthResponse(status="ok", version="1.0.0")


# ---------------------------------------------------------------------------
# Serve Frontend Static Files
# ---------------------------------------------------------------------------

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_path, "js")), name="js")

    @app.get("/", include_in_schema=False)
    def serve_landing():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/upload", include_in_schema=False)
    def serve_upload():
        return FileResponse(os.path.join(frontend_path, "upload.html"))

    @app.get("/dashboard", include_in_schema=False)
    def serve_dashboard():
        return FileResponse(os.path.join(frontend_path, "dashboard.html"))
