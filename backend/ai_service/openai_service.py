import logging

from django.conf import settings
from openai import OpenAI

from .base import AIService

logger = logging.getLogger(__name__)


class OpenAIService(AIService):
    """Implementación concreta del servicio de IA usando OpenAI."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate_response(
        self,
        document_content: str,
        conversation_history: list[dict],
        user_question: str,
    ) -> str:
        system_prompt = (
            "Eres un asistente especializado en analizar documentos. "
            "Solo puedes responder preguntas basadas estrictamente en el contenido "
            "del documento proporcionado. Si la pregunta no tiene relación con el "
            "documento, indica que no puedes responderla. "
            "Responde siempre en el mismo idioma que el usuario."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "system",
                "content": f"Contenido del documento:\n\n{document_content}",
            },
        ]

        # Agregar historial de conversación
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Agregar pregunta actual
        messages.append({"role": "user", "content": user_question})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.error("Error llamando a OpenAI: %s", exc)
            raise
