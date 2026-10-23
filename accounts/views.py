from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from .serializers import MeSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """Create an account. Password is hashed and never returned."""

    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    """The currently authenticated user."""

    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user
