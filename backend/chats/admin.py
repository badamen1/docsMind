from django.contrib import admin
from .models import Chat, Message

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "document", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("title", "user__email", "document__file_name")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("chat", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content", "chat__title")
