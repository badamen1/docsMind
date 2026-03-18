from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from documents.models import Document


class DocumentUploadTestCase(TestCase):
    """Tests básicos para subida y validación de documentos."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@docsmind.com", username="testuser", password="pass"
        )
        self.client.force_login(self.user)

    def test_upload_text_file(self):
        """Se puede subir un archivo .txt válido."""
        file = SimpleUploadedFile("test.txt", b"Contenido de prueba", content_type="text/plain")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Document.objects.filter(user=self.user).exists())

    def test_upload_invalid_extension(self):
        """Se rechaza un archivo con extensión no soportada."""
        file = SimpleUploadedFile("malicious.exe", b"fake content", content_type="application/octet-stream")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_path_traversal_sanitized(self):
        """Django sanitiza nombres con path traversal (quita directorios)."""
        file = SimpleUploadedFile("../../etc/passwd.txt", b"content", content_type="text/plain")
        # Django convierte '../../etc/passwd.txt' → 'passwd.txt' automáticamente
        self.assertNotIn("/", file.name)
        self.assertNotIn("..", file.name)

    def test_upload_unauthenticated(self):
        """Upload sin autenticación devuelve 403."""
        self.client.logout()
        file = SimpleUploadedFile("test.txt", b"Contenido", content_type="text/plain")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DocumentListTestCase(TestCase):
    """Tests básicos para listado de documentos."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@docsmind.com", username="testuser", password="pass"
        )
        self.client.force_login(self.user)

    def test_list_documents_empty(self):
        """Un usuario sin documentos recibe una lista vacía."""
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_documents_only_own(self):
        """Un usuario solo ve sus propios documentos."""
        other_user = User.objects.create_user(
            email="other@docsmind.com", username="other", password="pass"
        )
        Document.objects.create(
            user=other_user,
            file_name="other.txt",
            file_type=Document.FileType.TEXT,
            file_size=100,
        )
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
