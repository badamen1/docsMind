from django.urls import path

from .views import list_providers

urlpatterns = [
    path("providers/", list_providers, name="ai-providers"),
]
