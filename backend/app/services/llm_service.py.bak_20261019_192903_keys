"""Multi-provider LLM service with automatic fallback.

Providers (in priority order when set as primary):
  - Gemini (Google)
  - OpenAI (GPT)
  - Anthropic (Claude)

Any provider that raises is skipped, and the next configured one is used.
"""
from app.config import settings
from app.logger import logger


import time as _time_mod

_CIRCUIT_STATE = {}


def _in_cooldown(name):
    until = _CIRCUIT_STATE.get(name)
    if until is None:
        return False
    if _time_mod.time() >= until:
        del _CIRCUIT_STATE[name]
        return False
    return True


def _mark_cooldown(name, seconds):
    _CIRCUIT_STATE[name] = _time_mod.time() + seconds


def _clear_cooldown(name):
    _CIRCUIT_STATE.pop(name, None)


def _classify_error(msg):
    low = (msg or "").lower()
    if "429" in msg or "resource_exhausted" in low or "quota" in low or "rate limit" in low or "rate_limit" in low:
        return "rate_limited", 900
    if "503" in msg or "unavailable" in low or "502" in msg or "timeout" in low:
        return "transient", 120
    return "error", 300


class BaseProvider:
    name = "base"

    def is_configured(self) -> bool:
        return False

    def generate(self, prompt: str, context: str = "") -> str:
        raise NotImplementedError


class FreeLMProvider(BaseProvider):
    """Local freelm serve gateway -- pools free tiers with auto-failover."""
    name = "freelm"

    def __init__(self):
        self.client = None
        self.base_url = "http://127.0.0.1:4000/v1"
        self.api_key = "freelm"
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        except Exception as e:
            logger.warning(f"FreeLM init failed: {e}")
            self.client = None

    def is_configured(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, context: str = "") -> str:
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": (
                    "You are an innovation intelligence analyst with access to live platform data. "
                    "If the context has a STRUCTURED DATA section, use those exact numbers/titles. "
                    "If it has DOCUMENT EXCERPTS, cite them. If neither answers the question, say so."
                ),
            })
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="auto",
            messages=messages,
        )
        return response.choices[0].message.content


class GroqProvider(BaseProvider):
    """Groq API -- ultra-fast inference, OpenAI-compatible."""
    name = "groq"

    def __init__(self):
        self.client = None
        try:
            from openai import OpenAI
            if getattr(settings, "GROQ_API_KEY", ""):
                self.client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=settings.GROQ_API_KEY,
                )
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")
            self.client = None

    def is_configured(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, context: str = "") -> str:
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": (
                    "You are an innovation intelligence analyst with access to live platform data. "
                    "If the context has a STRUCTURED DATA section, use those exact numbers/titles. "
                    "If it has DOCUMENT EXCERPTS, cite them. If neither answers the question, say so."
                ),
            })
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=getattr(settings, "GROQ_MODEL", "openai/gpt-oss-20b"),
            messages=messages,
        )
        return response.choices[0].message.content


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types as _genai_types
                self.client = genai.Client(
                    api_key=settings.GEMINI_API_KEY,
                    http_options=_genai_types.HttpOptions(timeout=90_000),
                )
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")
                self.client = None

    def is_configured(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, context: str = "") -> str:
        import time
        full = prompt if not context else (
            f"You are an innovation intelligence analyst with access to live platform data.\n\n"
            f"{context}\n\n"
            f"User question: {prompt}\n\n"
            "Instructions:\n"
            "- If the STRUCTURED DATA section contains the answer, use those exact numbers and titles.\n"
            "- If the DOCUMENT EXCERPTS section is relevant, cite them.\n"
            "- If neither section answers the question, say so clearly instead of guessing.\n"
            "- Be concise. Use bullet points for lists."
        )
        # NO retries on 429 / quota -- daily quota will not recover in 2s.
        # Only retry transient 5xx / UNAVAILABLE (2 extra attempts max).
        import time as _t
        last_err = None
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=full,
                )
                return response.text
            except Exception as e:
                last_err = e
                msg = str(e)
                kind, _ = _classify_error(msg)
                if kind == "transient" and attempt < 2:
                    _t.sleep(2 ** attempt)
                    continue
                raise
        raise last_err


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                logger.warning("openai package not installed — skipping OpenAI provider")
                self.client = None
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e}")
                self.client = None

    def is_configured(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, context: str = "") -> str:
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": (
                    "You are an innovation intelligence analyst with access to live platform data. "
                    "If the context has a STRUCTURED DATA section, use those exact numbers/titles. "
                    "If it has DOCUMENT EXCERPTS, cite them. If neither answers the question, say so."
                ),
            })
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content


class OpenRouterProvider(BaseProvider):
    """OpenRouter -- OpenAI-compatible proxy for many models.

    Uses the same openai SDK with a different base_url. Model is user-configurable
    (e.g. 'google/gemini-2.0-flash-exp:free', 'anthropic/claude-3.5-haiku',
    'meta-llama/llama-3.3-70b-instruct:free').
    """
    name = "openrouter"

    def __init__(self):
        self.client = None
        if settings.OPENROUTER_API_KEY:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": "http://localhost",
                        "X-Title": "AI Opportunity Platform",
                    },
                )
            except ImportError:
                logger.warning("openai package not installed -- skipping OpenRouter provider")
                self.client = None
            except Exception as e:
                logger.warning(f"OpenRouter init failed: {e}")
                self.client = None

    def is_configured(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, context: str = "") -> str:
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": (
                    "You are an innovation intelligence analyst with access to live platform data. "
                    "If the context has a STRUCTURED DATA section, use those exact numbers/titles. "
                    "If it has DOCUMENT EXCERPTS, cite them. If neither answers the question, say so."
                ),
            })
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            except ImportError:
                logger.warning("anthropic package not installed — skipping Anthropic provider")
                self.client = None
            except Exception as e:
                logger.warning(f"Anthropic init failed: {e}")
                self.client = None

    def is_configured(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, context: str = "") -> str:
        system = (
            "You are an innovation intelligence analyst with access to live platform data. "
            "Use STRUCTURED DATA for exact numbers, DOCUMENT EXCERPTS for context. "
            "If neither answers the question, say so."
        )
        user_msg = prompt if not context else (
            f"Context information:\n{context}\n\nUser question: {prompt}\n\n"
            "Answer based on the context above. If the context is insufficient, say so."
        )
        response = self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content[0].text


class LLMService:
    """Multi-provider wrapper with fallback + status reporting.

    Singleton — one instance per process so that `last_used` accumulates
    across requests. Every caller gets the same object.
    """

    PROVIDER_ORDER = ["groq", "freelm", "gemini", "openrouter", "openai", "anthropic"]
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.providers = {
            "groq":       GroqProvider(),
            "freelm":     FreeLMProvider(),
            "gemini":     GeminiProvider(),
            "openrouter": OpenRouterProvider(),
            "openai":     OpenAIProvider(),
            "anthropic":  AnthropicProvider(),
        }
        self._last_used: str | None = None
        self._last_error: str | None = None
        self._initialized = True

    @property
    def enabled(self) -> bool:
        return any(p.is_configured() for p in self.providers.values())

    @property
    def last_used(self) -> str | None:
        return self._last_used

    def available_providers(self) -> list[str]:
        return [name for name, p in self.providers.items() if p.is_configured()]

    def _chain(self) -> list[BaseProvider]:
        """Primary first, then remaining configured providers.
        Skips providers currently in circuit-breaker cooldown. If ALL
        providers are cooling down, falls back to the ordered list so
        something is always tried (avoids hard-fail on cold cache)."""
        primary = (settings.LLM_PRIMARY_PROVIDER or "gemini").lower()
        ordered_names = [primary] + [n for n in self.PROVIDER_ORDER if n != primary]
        chain = []
        for name in ordered_names:
            p = self.providers.get(name)
            if p and p.is_configured() and not _in_cooldown(name):
                chain.append(p)
        if not chain:
            for name in ordered_names:
                p = self.providers.get(name)
                if p and p.is_configured():
                    chain.append(p)
        return chain

    def generate(self, prompt: str, context: str = "") -> str:
        chain = self._chain()
        if not chain:
            return (
                "AI service not configured. Add at least one API key in Admin → Config "
                "(GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)."
            )

        errors = []
        for provider in chain:
            try:
                result = provider.generate(prompt, context)
                self._last_used = provider.name
                if provider is not chain[0]:
                    logger.info(f"[LLM] Fallback to {provider.name} succeeded")
                return result
            except Exception as e:
                logger.warning(f"[LLM] {provider.name} failed: {e}")
                errors.append(f"{provider.name}: {e}")
                continue

        return f"All LLM providers failed. Errors: {'; '.join(errors)}"

    def explain_opportunity(self, opportunity_data: dict) -> str:
        prompt = f"""You are an innovation analyst. Explain why this opportunity scored the way it did.
Title: {opportunity_data.get('title')}
Demand: {opportunity_data.get('demand_score')}
Research Gap: {opportunity_data.get('research_gap_score')}
Trend: {opportunity_data.get('trend_score')}
Final Score: {opportunity_data.get('opportunity_score')}
Provide a concise 3-4 sentence explanation."""
        return self.generate(prompt)

    def generate_narrative(self, opportunities, gaps, trends, query: str = "") -> str:
        """
        Produce an executive-summary paragraph for a report.
        `opportunities`, `gaps`, `trends` are ORM rows or dicts.
        """
        def _o(o, key, default=0):
            return getattr(o, key, None) if hasattr(o, key) else o.get(key, default)

        # Build a compact factual brief
        lines = []
        if query:
            lines.append(f"Report scope: {query}")
        lines.append(f"Total opportunities analyzed: {len(opportunities)}")
        lines.append(f"Total research gaps: {len(gaps)}")
        lines.append(f"Total trends: {len(trends)}")
        lines.append("")

        if opportunities:
            lines.append("Top 5 opportunities by score:")
            for o in opportunities[:5]:
                lines.append(
                    f"  - {_o(o,'title','?')} | score={_o(o,'opportunity_score',0):.2f} | "
                    f"demand={_o(o,'demand_score',0):.2f} | "
                    f"gap={_o(o,'research_gap_score',0):.2f} | "
                    f"feasibility={_o(o,'feasibility_score',0):.2f}"
                )
            lines.append("")

        if gaps:
            lines.append("Top 3 research gaps:")
            for g in gaps[:3]:
                lines.append(f"  - {_o(g,'title','?')} (gap {_o(g,'gap_score',0):.2f})")
            lines.append("")

        if trends:
            seen = set()
            lines.append("Top 5 trends:")
            for t in trends:
                name = _o(t, "name", "?")
                if name in seen:
                    continue
                seen.add(name)
                lines.append(f"  - {name} (score {_o(t,'trend_score',0):.2f})")
                if len(seen) >= 5:
                    break
            lines.append("")

        brief = "\n".join(lines)

        prompt = (
            "Write a 4-6 sentence executive summary for an innovation intelligence report. "
            "Use ONLY the facts in the brief below. Do NOT invent names or numbers. "
            "Open with the strongest signal, then mention one research gap and one trend. "
            "End with a one-sentence recommendation. Do not use bullet points or headings, "
            "just one flowing paragraph.\n\n"
            f"FACTUAL BRIEF:\n{brief}"
        )

        try:
            result = self.generate(prompt)
            # LLMService.generate() returns an error string instead of raising.
            # Detect that and fall back to a graceful message.
            if result.startswith("All LLM providers failed") or result.startswith("AI service not configured"):
                logger.warning(f"[LLM] Narrative fallback triggered: {result[:100]}")
                return (
                    f"This report covers {len(opportunities)} opportunities, "
                    f"{len(gaps)} research gaps, and {len(trends)} trends discovered by the platform. "
                    f"The AI summary could not be generated right now (LLM provider unavailable). "
                    f"See the tables below for the full data breakdown."
                )
            return result
        except Exception as e:
            logger.error(f"[LLM] Narrative generation failed: {e}")
            return (
                f"This report covers {len(opportunities)} opportunities, "
                f"{len(gaps)} research gaps, and {len(trends)} trends discovered by the platform. "
                f"Narrative generation is currently unavailable."
            )

    def status(self) -> dict:
        cooldown = {}
        now = _time_mod.time()
        for name, until in list(_CIRCUIT_STATE.items()):
            remaining = int(until - now)
            if remaining > 0:
                cooldown[name] = f"{remaining}s"
            else:
                del _CIRCUIT_STATE[name]
        return {
            "enabled": self.enabled,
            "primary": settings.LLM_PRIMARY_PROVIDER,
            "available": [n for n in self.available_providers() if n not in cooldown],
            "cooldown": cooldown,
            "last_used": self._last_used,
            "last_error": getattr(self, "_last_error", None),
            "models": {
                "gemini": settings.GEMINI_MODEL,
                "openrouter": settings.OPENROUTER_MODEL,
                "openai": settings.OPENAI_MODEL,
                "anthropic": settings.ANTHROPIC_MODEL,
            },
        }
