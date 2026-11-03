from django.shortcuts import render
from django.http import HttpRequest, JsonResponse

def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})
