"""Multi-provider LLM service with automatic fallback.

Providers (in priority order when set as primary):
  - Gemini (Google)
  - OpenAI (GPT)
  - Anthropic (Claude)

Any provider that raises is skipped, and the next configured one is used.
"""
from app.config import settings
from app.logger import logger


class BaseProvider:
    name = "base"

    def is_configured(self) -> bool:
        return False

    def generate(self, prompt: str, context: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")
                self.client = None

    def is_configured(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, context: str = "") -> str:
        full = prompt if not context else (
            f"Context information:\n{context}\n\nUser question: {prompt}\n\n"
            "Answer based on the context above. If the context is insufficient, say so."
        )
        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=full,
        )
        return response.text


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
                    "You are an innovation analyst. Use the provided context to answer. "
                    "If the context is insufficient, say so."
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
        system = "You are an innovation analyst. Use the provided context to answer."
        user_msg = prompt if not context else (
            f"Context information:\n{context}\n\nUser question: {prompt}\n\n"
            "Answer based on the context above. If the context is insufficient, say so."
        )
        response = self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content[0].text


class LLMService:
    """Multi-provider wrapper with fallback + status reporting."""

    PROVIDER_ORDER = ["gemini", "openai", "anthropic"]

    def __init__(self):
        self.providers = {
            "gemini":    GeminiProvider(),
            "openai":    OpenAIProvider(),
            "anthropic": AnthropicProvider(),
        }
        self._last_used: str | None = None

    @property
    def enabled(self) -> bool:
        return any(p.is_configured() for p in self.providers.values())

    @property
    def last_used(self) -> str | None:
        return self._last_used

    def available_providers(self) -> list[str]:
        return [name for name, p in self.providers.items() if p.is_configured()]

    def _chain(self) -> list[BaseProvider]:
        """Primary first, then remaining configured providers."""
        primary = (settings.LLM_PRIMARY_PROVIDER or "gemini").lower()
        ordered_names = [primary] + [n for n in self.PROVIDER_ORDER if n != primary]
        chain = []
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

    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "primary": settings.LLM_PRIMARY_PROVIDER,
            "available": self.available_providers(),
            "last_used": self._last_used,
            "models": {
                "gemini": settings.GEMINI_MODEL,
                "openai": settings.OPENAI_MODEL,
                "anthropic": settings.ANTHROPIC_MODEL,
            },
        }
