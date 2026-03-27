from rest_framework import serializers

from .models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializer para un mensaje individual."""

    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = fields


class ChatListSerializer(serializers.ModelSerializer):
    """Serializer para listar chats (sin mensajes)."""

    class Meta:
        model = Chat
        fields = ["id", "title", "document", "created_at", "updated_at"]
        read_only_fields = fields


class ChatDetailSerializer(serializers.ModelSerializer):
    """Serializer para ver un chat con todos sus mensajes."""

    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ["id", "title", "document", "messages", "created_at", "updated_at"]
        read_only_fields = fields


class CreateChatSerializer(serializers.Serializer):
    """Serializer para crear un nuevo chat con un documento."""

    document_id = serializers.UUIDField()


class SendMessageSerializer(serializers.Serializer):
    """Serializer para validar el envío de un mensaje."""

    content = serializers.CharField(max_length=5000)
    provider = serializers.ChoiceField(
        choices=[("openai", "OpenAI"), ("gemini", "Gemini")],
        default="gemini",
        required=False,
    )
