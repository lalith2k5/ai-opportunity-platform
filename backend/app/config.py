import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Environment
    # DEV_MODE=true  -> forgot-password returns the reset token in the JSON response (local dev)
    # DEV_MODE=false -> token is only logged server-side; response is neutral (production)
    DEV_MODE: bool = os.getenv("DEV_MODE", "true").lower() in ("1", "true", "yes")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/ai_opportunity_db")

    # LLM providers
    LLM_PRIMARY_PROVIDER: str = os.getenv("LLM_PRIMARY_PROVIDER", "gemini")  # gemini | openai | anthropic

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

    # Data sources
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    # PatentsView (https://patentsview.org/apis/keyrequest) — blank disables patents source
    PATENTSVIEW_API_KEY: str = os.getenv("PATENTSVIEW_API_KEY", "")
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "ai-opportunity-platform/1.0")

    # Vector store
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Challenge portals — industry / gov problem statements (ProblemProfile)
    ENABLE_CHALLENGE_PORTALS: bool = os.getenv("ENABLE_CHALLENGE_PORTALS", "true").lower() in ("1", "true", "yes")
    CHALLENGE_PORTAL_CAP: int = int(os.getenv("CHALLENGE_PORTAL_CAP", "20"))
    PROBLEM_EXTRACTION_CAP: int = int(os.getenv("PROBLEM_EXTRACTION_CAP", "8"))

    # Per-source problem extraction caps (each extraction = 1 LLM call).
    # Tuned for Gemini free-tier rate limits; raise in .env if you have headroom.
    PROBLEM_EXTRACTION_CAP_GITHUB: int = int(os.getenv("PROBLEM_EXTRACTION_CAP_GITHUB", "3"))
    PROBLEM_EXTRACTION_CAP_ARXIV: int = int(os.getenv("PROBLEM_EXTRACTION_CAP_ARXIV", "2"))
    PROBLEM_EXTRACTION_CAP_NEWS: int = int(os.getenv("PROBLEM_EXTRACTION_CAP_NEWS", "1"))
    PROBLEM_EXTRACTION_CAP_PATENTS: int = int(os.getenv("PROBLEM_EXTRACTION_CAP_PATENTS", "2"))

settings = Settings()
