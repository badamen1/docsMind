"""Clase abstracta que define el contrato para servicios de IA (DIP)."""

from abc import ABC, abstractmethod


class AIService(ABC):
    """
    Interfaz para servicios de IA.
    Permite intercambiar implementaciones (OpenAI, Anthropic, local, etc.)
    sin modificar el código que consume el servicio.
    """

    @abstractmethod
    def generate_response(
        self,
        document_content: str,
        conversation_history: list[dict],
        user_question: str,
    ) -> str:
        """
        Genera una respuesta basada en el documento y la conversación.

        Args:
            document_content: Contenido Markdown del documento.
            conversation_history: Lista de mensajes previos [{"role": ..., "content": ...}].
            user_question: Pregunta actual del usuario.

        Returns:
            Respuesta generada por la IA.
        """
        ...
