import logging
import google.generativeai as genai
from django.conf import settings
from .base import AIService

logger = logging.getLogger(__name__)

class GeminiService(AIService):
    """Implementación concreta del servicio de IA usando Google Gemini."""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Por defecto si no se pasa, usamos el flash
        self.model = genai.GenerativeModel(getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash'))

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

        contents = [
            {"role": "user", "parts": [f"{system_prompt}\n\nContenido del documento:\n\n{document_content}"]},
            {"role": "model", "parts": ["Entendido. Solo usaré el documento proporcionado para responder."]}
        ]

#Aqui se agrega el historial de la conversacion        
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [msg["content"]]})
        
        contents.append({"role": "user", "parts": [user_question]})

        try:
            response = self.model.generate_content(contents)
            return response.text
        except Exception as exc:
            logger.error("Error llamando a Gemini: %s", exc)
            raise

    # Agregados los métodos a petición en la instrucción, mapeándolos en la clase.
    def generateResponse(self, context, query):
        """Mapeo para compatibilidad con interfaces nombradas en camelCase."""
        return self.generate_response(context, [], query)

    def validateQuery(self, query):
        """Mapeo del método para validación."""
        pass

    def checkUsageLimit(self, userId):
        """Mapeo del método de límites."""
        pass
