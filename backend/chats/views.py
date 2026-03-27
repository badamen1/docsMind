import logging

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_service.factory import get_ai_service
from documents.models import Document

from .models import Chat, Message
from .serializers import (
    ChatDetailSerializer,
    ChatListSerializer,
    CreateChatSerializer,
    SendMessageSerializer,
)

logger = logging.getLogger(__name__)


class UserFilteredMixin:
    """Filtra el queryset para mostrar solo los objetos del usuario autenticado."""

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)


class ChatListView(UserFilteredMixin, generics.ListAPIView):
    """GET /api/chats/ — lista chats del usuario."""

    serializer_class = ChatListSerializer
    permission_classes = [IsAuthenticated]


class CreateChatView(APIView):
    """POST /api/chats/ — crear un chat nuevo para un documento."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_id = serializer.validated_data["document_id"]

        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"detail": "Documento no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Reutilizar chat existente o crear uno nuevo
        chat = Chat.objects.filter(
            user=request.user, document=document
        ).order_by("-updated_at").first()

        created = False
        if not chat:
            chat = Chat.objects.create(
                user=request.user,
                document=document,
                title=f"Chat - {document.file_name}",
            )
            created = True

        return Response(
            ChatDetailSerializer(chat).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ChatDetailView(UserFilteredMixin, generics.RetrieveDestroyAPIView):
    """
    GET    /api/chats/{id}/ — detalle del chat con historial de mensajes.
    DELETE /api/chats/{id}/ — eliminar un chat.
    """

    serializer_class = ChatDetailSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]


class SendMessageView(APIView):
    """POST /api/chats/{id}/messages/ — enviar pregunta y recibir respuesta de IA."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        # Obtener el chat (solo del usuario autenticado)
        try:
            chat = Chat.objects.select_related("document").get(
                id=id, user=request.user
            )
        except Chat.DoesNotExist:
            return Response(
                {"detail": "Chat no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validar el mensaje del usuario
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_content = serializer.validated_data["content"]
        # Obtener proveedor del request (opcional)  
        provider = serializer.validated_data.get("provider", "gemini")

        # Verificar que el documento está procesado
        document = chat.document
        if document.status != Document.Status.COMPLETED:
            return Response(
                {"detail": "El documento aún no ha sido procesado. Intenta más tarde."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener historial de conversación
        history = list(
            chat.messages.values("role", "content").order_by("created_at")
        )

        # Guardar mensaje del usuario
        Message.objects.create(
            chat=chat, role=Message.Role.USER, content=user_content
        )

        # Llamar al servicio de IA con el proveedor seleccionado
        try:
            ai_service = get_ai_service(provider)
            ai_response = ai_service.generate_response(
                document_content=document.markdown_content,
                conversation_history=history,
                user_question=user_content,
            )
        except Exception as exc:
            logger.error("Error generando respuesta de IA para chat %s: %s", id, exc)
            return Response(
                {"detail": "Error al generar la respuesta. Intenta más tarde."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Guardar respuesta del asistente
        assistant_message = Message.objects.create(
            chat=chat, role=Message.Role.ASSISTANT, content=ai_response
        )

        from .serializers import MessageSerializer
        return Response(
            MessageSerializer(assistant_message).data,
            status=status.HTTP_201_CREATED,
        )
