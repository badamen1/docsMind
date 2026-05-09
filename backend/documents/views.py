import logging

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Document
from .ocr import get_ocr_service
from .services import DocumentService

logger = logging.getLogger(__name__)


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """Sube un documento, detecta su tipo, verifica límites y lo procesa a Markdown."""
    file = request.FILES.get("file")
    if not file:
        return Response(
            {"error": "No se envió ningún archivo."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        file_type = Document.detect_file_type(file.name)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        DocumentService.check_upload_limits(request.user, file.size)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)

    document = Document.objects.create(
        user=request.user,
        file=file,
        file_name=file.name,
        file_type=file_type,
        file_size=file.size,
    )

    ocr_service = get_ocr_service(request.user)
    DocumentService.process_document(document, ocr_service)

    if document.status == Document.Status.FAILED:
        return Response(
            {"error": document.error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            "id": str(document.id),
            "file_name": document.file_name,
            "file_type": document.file_type,
            "status": document.status,
            "markdown_content": document.markdown_content,
            "error_message": document.error_message,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_documents(request):
    """Lista todos los documentos del usuario autenticado."""
    documents = Document.objects.filter(user=request.user)
    data = [
        {
            "id": str(doc.id),
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "status": doc.status,
            "file_size": doc.file_size,
            "created_at": doc.created_at.isoformat(),
        }
        for doc in documents
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document(request, document_id):
    """Obtiene un documento específico con su contenido Markdown."""
    try:
        document = Document.objects.get(id=document_id, user=request.user)
    except Document.DoesNotExist:
        return Response(
            {"error": "Documento no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "id": str(document.id),
            "file_name": document.file_name,
            "file_type": document.file_type,
            "status": document.status,
            "file_size": document.file_size,
            "markdown_content": document.markdown_content,
            "error_message": document.error_message,
            "created_at": document.created_at.isoformat(),
        }
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    """Elimina un documento del usuario."""
    try:
        document = Document.objects.get(id=document_id, user=request.user)
    except Document.DoesNotExist:
        return Response(
            {"error": "Documento no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    document.file.delete()
    document.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
