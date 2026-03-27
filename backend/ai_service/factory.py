"""Factory que resuelve qué implementación de AIService usar según settings."""

from django.conf import settings

from .base import AIService


def get_ai_service(provider: str | None = None) -> AIService:
    """
    Retorna la instancia del servicio de IA.

    Args:
        provider: "openai" | "gemini". Si es None, usa settings.AI_PROVIDER.
    """
    provider = (provider or getattr(settings, "AI_PROVIDER", "gemini")).lower()

    if provider == "openai":
        from .openai_service import OpenAIService
        return OpenAIService()
    #Default: Gemini
    from .gemini_service import GeminiService
    return GeminiService()
