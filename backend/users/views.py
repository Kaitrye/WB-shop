import logging

from django.http import HttpRequest, JsonResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.serializers import RegisterSerializer, UserSerializer


logger = logging.getLogger("shop")


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        logger.info("event=user_registered user_id=%s", user.pk)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
