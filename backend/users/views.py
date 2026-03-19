from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken


@method_decorator(csrf_exempt, name='dispatch')
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="post")
class UserLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # En JWT no hay sesión server-side; el frontend borra tokens.
        return Response({"detail": "OK"}, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    """GET /api/me/ -> devuelve datos del usuario logueado."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class SubscriptionDetailView(APIView):
    """GET /api/subscription/ -> devuelve el plan y uso actual."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = getattr(request.user, "subscription", None)
        if not sub:
            return Response(
                {"detail": "No subscription found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "plan": sub.plan.name if sub.plan else "Free",
                "plan_type": sub.plan.plan_type if sub.plan else "free",
                "status": sub.status,
                "price": str(sub.plan.price) if sub.plan else "0.00",
                "max_documents": sub.plan.max_documents if sub.plan else 5,
                "max_storage_mb": sub.plan.max_storage_mb if sub.plan else 10,
                "is_active": sub.status == "active",
            }
        )