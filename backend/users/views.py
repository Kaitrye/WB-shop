from django.shortcuts import render
from django.http import HttpRequest, JsonResponse

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.serializers import RegisterSerializer, UserSerializer

def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
