from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import MagicMock, patch

from users.models import User
from documents.models import Document
from chats.models import Chat, Message
from subscription.models import Plan


class ChatModelTestCase(TestCase):
    """Tests para los modelos Chat y Message."""

    def setUp(self):
        Plan.objects.create(
            plan_type=Plan.PlanType.FREE,
            name="Free",
            price="0.00",
            description="Plan gratuito",
            max_documents=5,
            max_storage_mb=10,
        )
        self.user = User.objects.create_user(
            email="test@docsmind.com",
            username="testuser",
            password="TestPass123!",
        )
        self.document = Document.objects.create(
            user=self.user,
            file_name="test.txt",
            file_type=Document.FileType.TEXT,
            file_size=100,
            status=Document.Status.COMPLETED,
            markdown_content="Contenido de prueba del documento.",
        )
        self.chat = Chat.objects.create(
            user=self.user,
            document=self.document,
            title="Chat de prueba",
        )

    def test_chat_str(self):
        """El string del chat incluye el título."""
        self.assertIn("Chat de prueba", str(self.chat))

    def test_message_str(self):
        """El string del mensaje incluye el rol y contenido."""
        msg = Message.objects.create(
            chat=self.chat,
            role=Message.Role.USER,
            content="¿De qué trata el documento?",
        )
        self.assertIn("user", str(msg))

    def test_messages_ordering(self):
        """Los mensajes se ordenan por fecha de creación (ascendente)."""
        msg1 = Message.objects.create(
            chat=self.chat, role=Message.Role.USER, content="Primera pregunta"
        )
        msg2 = Message.objects.create(
            chat=self.chat, role=Message.Role.ASSISTANT, content="Primera respuesta"
        )
        messages = list(self.chat.messages.all())
        self.assertEqual(messages[0].id, msg1.id)
        self.assertEqual(messages[1].id, msg2.id)


class ChatAPITestCase(TestCase):
    """Tests para los endpoints de Chat."""

    def setUp(self):
        Plan.objects.create(
            plan_type=Plan.PlanType.FREE,
            name="Free",
            price="0.00",
            description="Plan gratuito",
            max_documents=5,
            max_storage_mb=10,
        )
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@docsmind.com",
            username="testuser",
            password="TestPass123!",
        )
        self.other_user = User.objects.create_user(
            email="other@docsmind.com",
            username="otheruser",
            password="TestPass123!",
        )
        self.client.force_login(self.user)
        self.document = Document.objects.create(
            user=self.user,
            file_name="test.txt",
            file_type=Document.FileType.TEXT,
            file_size=100,
            status=Document.Status.COMPLETED,
            markdown_content="Contenido de prueba del documento.",
        )
        self.chat = Chat.objects.create(
            user=self.user,
            document=self.document,
            title="Mi Chat",
        )

    def test_list_chats_authenticated(self):
        """Un usuario ve solo sus propios chats, no los de otros."""
        # Chat de otro usuario no debería aparecer
        other_doc = Document.objects.create(
            user=self.other_user,
            file_name="other.txt",
            file_type=Document.FileType.TEXT,
            file_size=50,
        )
        Chat.objects.create(
            user=self.other_user,
            document=other_doc,
            title="Chat de otro usuario",
        )
        response = self.client.get("/api/chats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que ningún chat del otro usuario aparece en la respuesta
        titles = [chat["title"] for chat in response.data]
        self.assertIn("Mi Chat", titles)
        self.assertNotIn("Chat de otro usuario", titles)

    def test_list_chats_unauthenticated(self):
        """Sin autenticación devuelve 403."""
        self.client.logout()
        response = self.client.get("/api/chats/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_chat_detail(self):
        """Se puede obtener el detalle de un chat con sus mensajes."""
        Message.objects.create(
            chat=self.chat,
            role=Message.Role.USER,
            content="¿Qué dice el documento?",
        )
        response = self.client.get(f"/api/chats/{self.chat.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Mi Chat")
        self.assertEqual(len(response.data["messages"]), 1)

    def test_delete_chat(self):
        """Un usuario puede eliminar su propio chat."""
        response = self.client.delete(f"/api/chats/{self.chat.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Chat.objects.filter(id=self.chat.id).exists())

    def test_send_message_document_not_ready(self):
        """Enviar mensaje falla si el documento no está procesado."""
        pending_doc = Document.objects.create(
            user=self.user,
            file_name="pending.txt",
            file_type=Document.FileType.TEXT,
            file_size=100,
            status=Document.Status.PENDING,
        )
        pending_chat = Chat.objects.create(
            user=self.user,
            document=pending_doc,
            title="Chat pendiente",
        )
        response = self.client.post(
            f"/api/chats/{pending_chat.id}/messages/",
            {"content": "Pregunta al documento pendiente"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("chats.views.ai_service.generate_response", return_value="Respuesta de la IA")
    def test_send_message_success(self, mock_ai):
        """Enviar un mensaje devuelve la respuesta de la IA."""
        response = self.client.post(
            f"/api/chats/{self.chat.id}/messages/",
            {"content": "¿De qué trata el documento?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Respuesta de la IA")
        self.assertEqual(response.data["role"], Message.Role.ASSISTANT)
        # Verificar que se guardaron ambos mensajes (user + assistant)
        self.assertEqual(self.chat.messages.count(), 2)


class GeminiModelSelectionTestCase(TestCase):
    """Tests para la selección de modelo Gemini según el plan."""

    def setUp(self):
        self.free_plan, _ = Plan.objects.get_or_create(
            plan_type=Plan.PlanType.FREE,
            defaults={
                "name": "Free", "price": "0.00",
                "description": "Plan gratuito", "max_documents": 5, "max_storage_mb": 10,
            },
        )
        self.pro_plan, _ = Plan.objects.get_or_create(
            plan_type=Plan.PlanType.PRO,
            defaults={
                "name": "Pro", "price": "9.99",
                "description": "Plan pro", "max_documents": 100, "max_storage_mb": 1024,
            },
        )
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="geminitest@test.com", username="geminitest", password="pass"
        )
        self.client.force_authenticate(user=self.user)
        self.document = Document.objects.create(
            user=self.user,
            file_name="test.txt",
            file_type=Document.FileType.TEXT,
            file_size=100,
            status=Document.Status.COMPLETED,
            markdown_content="Contenido de prueba.",
        )
        self.chat = Chat.objects.create(
            user=self.user, document=self.document, title="Chat test"
        )

    def test_free_user_cannot_select_gemini_model(self):
        """Usuario Free recibe 403 al especificar gemini_model."""
        response = self.client.post(
            f"/api/chats/{self.chat.id}/messages/",
            {"content": "Pregunta", "gemini_model": "gemini-2.5-pro"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Plan Pro", response.data["detail"])

    @patch("chats.views.get_ai_service")
    def test_pro_user_can_select_gemini_model(self, mock_get_ai):
        """Usuario Pro puede elegir gemini-2.5-pro y se pasa al factory."""
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Respuesta Pro"
        mock_get_ai.return_value = mock_service

        self.user.subscription.plan = self.pro_plan
        self.user.subscription.save(update_fields=["plan", "updated_at"])

        response = self.client.post(
            f"/api/chats/{self.chat.id}/messages/",
            {"content": "Pregunta", "gemini_model": "gemini-2.5-pro"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_get_ai.assert_called_once_with("gemini", model="gemini-2.5-pro")

    @patch("chats.views.get_ai_service")
    def test_free_user_without_model_field_uses_default(self, mock_get_ai):
        """Usuario Free sin gemini_model obtiene 200 con modelo por defecto."""
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Respuesta Flash"
        mock_get_ai.return_value = mock_service

        response = self.client.post(
            f"/api/chats/{self.chat.id}/messages/",
            {"content": "Pregunta"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_get_ai.assert_called_once_with("gemini", model=None)
