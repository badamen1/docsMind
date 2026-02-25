from django.contrib import admin

from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "plan_type", "price", "max_documents", "max_storage_mb")
    ordering = ("price",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "started_at", "expires_at")
    list_filter = ("status", "plan__plan_type")
    search_fields = ("user__email",)
    readonly_fields = ("created_at", "updated_at", "started_at")
