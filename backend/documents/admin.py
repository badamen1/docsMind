from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("file_name", "user", "file_type", "status", "file_size", "created_at")
    list_filter = ("status", "file_type")
    search_fields = ("file_name", "user__email")
    readonly_fields = ("id", "file_size", "markdown_content", "status", "error_message", "created_at", "updated_at")
    ordering = ("-created_at",)
