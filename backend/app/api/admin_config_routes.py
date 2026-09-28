import re
from pathlib import Path
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models
from app.auth.dependencies import require_role
from app.config import settings
from app.logger import logger

router = APIRouter(prefix="/admin", tags=["admin-config"])

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

# Which keys we allow the admin to edit (and how to mask them)
EDITABLE_KEYS = {
    # LLM providers
    "LLM_PRIMARY_PROVIDER":{"label": "Primary LLM provider",   "provider": "System",   "url": ""},
    "GEMINI_API_KEY":      {"label": "Google Gemini API key",  "provider": "Google",   "url": "https://aistudio.google.com/apikey"},
    "GEMINI_MODEL":        {"label": "Gemini model name",      "provider": "Google",   "url": ""},
    "OPENAI_API_KEY":      {"label": "OpenAI API key",         "provider": "OpenAI",   "url": "https://platform.openai.com/api-keys"},
    "OPENAI_MODEL":        {"label": "OpenAI model name",      "provider": "OpenAI",   "url": ""},
    "ANTHROPIC_API_KEY":   {"label": "Anthropic API key",      "provider": "Anthropic","url": "https://console.anthropic.com/settings/keys"},
    "ANTHROPIC_MODEL":     {"label": "Anthropic model name",   "provider": "Anthropic","url": ""},
    # Data sources
    "GITHUB_TOKEN":        {"label": "GitHub Personal token",  "provider": "GitHub",   "url": "https://github.com/settings/tokens"},
    "PATENTSVIEW_API_KEY": {"label": "PatentsView API key",    "provider": "PatentsView", "url": "https://patentsview.org/apis/keyrequest"},
    "REDDIT_CLIENT_ID":    {"label": "Reddit Client ID",       "provider": "Reddit",   "url": "https://www.reddit.com/prefs/apps"},
    "REDDIT_CLIENT_SECRET":{"label": "Reddit Client Secret",   "provider": "Reddit",   "url": "https://www.reddit.com/prefs/apps"},
    "REDDIT_USER_AGENT":   {"label": "Reddit User Agent",      "provider": "Reddit",   "url": ""},
    # Infrastructure
    "DATABASE_URL":        {"label": "PostgreSQL connection",  "provider": "Postgres", "url": ""},
    "CHROMA_PERSIST_DIR":  {"label": "ChromaDB storage path",  "provider": "ChromaDB", "url": ""},
}

def _mask(value: str) -> str:
    """Show enough to recognize the key, mask the rest."""
    if not value:
        return ""
    if len(value) <= 8:
        return "•" * len(value)
    return value[:6] + "•" * min(20, len(value) - 10) + value[-4:]


def _read_env_file() -> Dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    out: Dict[str, str] = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$', line)
        if not m:
            continue
        key = m.group(1)
        val = m.group(2).strip().strip('"').strip("'")
        out[key] = val
    return out


def _write_env_key(key: str, value: str):
    """Safely update a single key in .env, preserving everything else."""
    if not ENV_PATH.exists():
        ENV_PATH.write_text(f'{key}="{value}"\n')
        return

    lines = ENV_PATH.read_text().splitlines()
    pattern = re.compile(r'^\s*' + re.escape(key) + r'\s*=')
    found = False
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f'{key}="{value}"'
            found = True
            break
    if not found:
        lines.append(f'{key}="{value}"')
    ENV_PATH.write_text("\n".join(lines) + "\n")


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("/settings")
def get_settings(
    user: models.User = Depends(require_role("admin")),
):
    """Return masked config for editable keys + status flags."""
    env = _read_env_file()
    # Merge with current runtime settings (in case .env missing)
    current = {
        "LLM_PRIMARY_PROVIDER": settings.LLM_PRIMARY_PROVIDER,
        "GEMINI_API_KEY":       settings.GEMINI_API_KEY,
        "GEMINI_MODEL":         settings.GEMINI_MODEL,
        "OPENAI_API_KEY":       settings.OPENAI_API_KEY,
        "OPENAI_MODEL":         settings.OPENAI_MODEL,
        "ANTHROPIC_API_KEY":    settings.ANTHROPIC_API_KEY,
        "ANTHROPIC_MODEL":      settings.ANTHROPIC_MODEL,
        "GITHUB_TOKEN":         settings.GITHUB_TOKEN,
        "PATENTSVIEW_API_KEY":  settings.PATENTSVIEW_API_KEY,
        "REDDIT_CLIENT_ID":     settings.REDDIT_CLIENT_ID,
        "REDDIT_CLIENT_SECRET": settings.REDDIT_CLIENT_SECRET,
        "REDDIT_USER_AGENT":    settings.REDDIT_USER_AGENT,
        "DATABASE_URL":         settings.DATABASE_URL,
        "CHROMA_PERSIST_DIR":   settings.CHROMA_PERSIST_DIR,
    }
    items = []
    for key, meta in EDITABLE_KEYS.items():
        raw = env.get(key, current.get(key, ""))
        items.append({
            "key": key,
            "label": meta["label"],
            "provider": meta["provider"],
            "docs_url": meta["url"],
            "masked": _mask(raw),
            "is_set": bool(raw),
            "is_env_managed": key in env,
            "hint": "Restart backend after changes" if key in ("GEMINI_API_KEY", "DATABASE_URL", "CHROMA_PERSIST_DIR") else "Applies on next API call",
        })
    return {"items": items, "env_path": str(ENV_PATH)}


@router.patch("/settings")
def update_setting(
    payload: SettingUpdate,
    user: models.User = Depends(require_role("admin")),
):
    if payload.key not in EDITABLE_KEYS:
        raise HTTPException(400, f"Key '{payload.key}' is not editable")
    value = (payload.value or "").strip()
    try:
        _write_env_key(payload.key, value)
        # Hot-update runtime settings so most changes work without restart
        try:
            setattr(settings, payload.key, value)
        except Exception:
            pass
        logger.info(f"[Admin] Setting updated: {payload.key} (masked: {_mask(value)})")
        return {
            "ok": True,
            "key": payload.key,
            "masked": _mask(value),
            "is_set": bool(value),
            "restart_required": payload.key in ("GEMINI_API_KEY", "DATABASE_URL", "CHROMA_PERSIST_DIR"),
        }
    except Exception as e:
        logger.error(f"[Admin] Failed to update {payload.key}: {e}")
        raise HTTPException(500, f"Failed to write setting: {e}")


@router.get("/sync/status")
def sync_status(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    """Per-source counts + last raw doc inserted."""
    rows = (
        db.query(
            models.RawDocument.source,
            func.count(models.RawDocument.id).label("count"),
            func.max(models.RawDocument.collected_at).label("last"),
        )
        .group_by(models.RawDocument.source)
        .all()
    )
    source_map = {r[0] or "unknown": {"count": r[1], "last": r[2]} for r in rows}

    # Reddit is configured?
    reddit_configured = bool(settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET)
    github_configured = bool(settings.GITHUB_TOKEN)
    gemini_configured = bool(settings.GEMINI_API_KEY)
    patents_configured = bool(settings.PATENTSVIEW_API_KEY)

    def src(name, configured, default_enabled=True):
        info = source_map.get(name, {"count": 0, "last": None})
        return {
            "source": name,
            "documents": info["count"],
            "last_collected": info["last"],
            "configured": configured,
            "enabled": default_enabled and configured,
        }

    return {
        "sources": [
            src("github",   True),           # GitHub works without token (rate-limited)
            src("arxiv",    True),           # Always available
            src("news",     True),           # RSS — always available
            src("rd_cells", True),           # Corporate/academic/gov R&D lab feeds
            src("patents",  patents_configured),  # PatentsView (opt-in; disabled if PATENTSVIEW_API_KEY is blank)
            src("reddit",   reddit_configured),
        ],
        "ai": {
            "gemini": gemini_configured,
            "embeddings": True,            # SentenceTransformers local
        },
        "database": {
            "raw_docs": db.query(models.RawDocument).count(),
            "processed_docs": db.query(models.ProcessedDocument).count(),
            "opportunities": db.query(models.Opportunity).count(),
            "kg_nodes": db.query(models.KnowledgeGraphNode).count(),
            "kg_edges": db.query(models.KnowledgeGraphEdge).count(),
        },
    }


class SyncRequest(BaseModel):
    topic: str
    mode: Optional[str] = "quick"  # quick or deep
    sources: Optional[list] = None  # e.g. ["github","arxiv"]; None = all


@router.post("/sync/trigger")
def sync_trigger(
    payload: SyncRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    """Trigger a pipeline run for a specific topic. Runs in background."""
    from app.agents.orchestrator import OrchestratorAgent

    topic = (payload.topic or "").strip()
    if not topic:
        raise HTTPException(400, "Topic is required")
    mode = payload.mode if payload.mode in ("quick", "deep") else "quick"

    logger.info(f"[Admin] Sync triggered: topic='{topic}', mode={mode}, by={user.email}")

    # Run synchronously for simplicity (frontend shows spinner)
    try:
        orch = OrchestratorAgent()
        result = orch.run_full_pipeline(topic, user_id=user.id, mode=mode)
        return {
            "ok": True,
            "topic": topic,
            "mode": mode,
            "documents_count": result["documents_count"],
            "opportunities": len(result["opportunities"]),
            "clusters": len(result["clusters"]),
            "gaps": len(result["research_gaps"]),
            "kg_stats": result["knowledge_graph"],
        }
    except RuntimeError as e:
        # Pipeline lock held -- this is a "busy" state, not a server error
        logger.warning(f"[Admin] Sync refused (pipeline busy): {e}")
        raise HTTPException(409, str(e))
    except Exception as e:
        logger.exception(f"[Admin] Sync failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/pipeline/status")
def pipeline_status(
    _=Depends(require_role("admin")),
):
    """Read-only status of the pipeline lock (SRS 32 -- continuous update)."""
    from app.agents.orchestrator import get_pipeline_status
    return get_pipeline_status()


@router.get("/data-sources")
def list_data_sources(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    """SRS FR-01: registered data sources with live document counts."""
    rows = (
        db.query(models.DataSource)
        .order_by(models.DataSource.name)
        .all()
    )
    # Doc count per source (raw_documents.source == DataSource.name)
    from sqlalchemy import func
    counts = dict(
        db.query(
            models.RawDocument.source,
            func.count(models.RawDocument.id),
        ).group_by(models.RawDocument.source).all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "source_type": r.source_type or "",
            "is_active": bool(r.is_active),
            "last_fetched": r.last_fetched.isoformat() if r.last_fetched else None,
            "document_count": counts.get(r.name, 0),
        }
        for r in rows
    ]


class DataSourceToggle(BaseModel):
    is_active: bool


@router.patch("/data-sources/{source_id}")
def toggle_data_source(
    source_id: int,
    payload: DataSourceToggle,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    """Enable/disable a registered data source (SRS FR-01)."""
    row = db.query(models.DataSource).filter(models.DataSource.id == source_id).first()
    if not row:
        raise HTTPException(404, "Data source not found")
    row.is_active = payload.is_active
    db.commit()
    logger.info(
        f"[Admin] DataSource '{row.name}' -> is_active={row.is_active} "
        f"by {user.email}"
    )
    return {"id": row.id, "name": row.name, "is_active": bool(row.is_active)}


@router.get("/data-sources/active-names")
def active_source_names(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    """Return the set of currently-active source names for pipeline gating."""
    rows = (
        db.query(models.DataSource.name)
        .filter(models.DataSource.is_active == True)  # noqa: E712
        .all()
    )
    return {"active": sorted(r[0] for r in rows)}


@router.get("/llm/status")
def llm_status(
    user: models.User = Depends(require_role("admin")),
):
    """Report which LLM providers are configured and which is primary."""
    from app.services.llm_service import LLMService
    svc = LLMService()
    return svc.status()
