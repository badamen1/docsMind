"""Endpoints para el módulo de IA."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

AI_PROVIDERS = [
    {
        "id": "gemini",
        "name": "Gemini 2.5 Flash",
        "is_premium": False,
    },
    {
        "id": "openai",
        "name": "GPT-4o mini",
        "is_premium": True,
    },
]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_providers(request):
    """GET /api/ai/providers/ — lista de proveedores de IA disponibles."""
    return Response(AI_PROVIDERS)
