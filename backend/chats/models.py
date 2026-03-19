import uuid

from django.conf import settings
from django.db import models

from documents.models import Document


class Chat(models.Model):
    """Chat asociado a un documento."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chats",
    )
    # ForeignKey (no OneToOne) para soportar 1:many en el futuro
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chats",
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chat"
        verbose_name_plural = "Chats"

    def __str__(self):
        return f"Chat: {self.title}"


class Message(models.Model):
    """Mensaje dentro de un chat."""

    class Role(models.TextChoices):
        USER = "user", "Usuario"
        ASSISTANT = "assistant", "Asistente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}"
