from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skillbridge.db")

# SQLite-specific connection args (needed for multi-threaded FastAPI)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# Database Models
# ---------------------------------------------------------------------------

class AnalysisRecord(Base):
    """Stores each resume analysis result for history retrieval."""
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, index=True)          # UUID v4
    session_token = Column(String, index=True)                  # Links to user session
    target_role = Column(String, nullable=False)
    candidate_name = Column(String, default="Anonymous")
    overall_score = Column(Integer, nullable=False)
    full_result_json = Column(Text, nullable=False)             # Full JSON response cached
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------------------------

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Dependency — used in FastAPI route injection
# ---------------------------------------------------------------------------

def get_db():
    """Yield a database session and ensure it closes after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
