from django.shortcuts import render

# Create your views here.
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer, ApiCredentialTestSerializer, ApiCredentialSaveSerializer
from .models import ApiCredential

# Bybit check
from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user: User = s.save()
        return Response({"id": user.id, "username": user.username}, status=201)

class CredentialTestView(APIView):
    def post(self, request):
        s = ApiCredentialTestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        api_key = s.validated_data["api_key"].strip()
        api_secret = s.validated_data["api_secret"].strip()
        is_testnet = s.validated_data["is_testnet"]

        sess = HTTP(api_key=api_key, api_secret=api_secret, testnet=is_testnet)
        try:
            info = sess.get_api_key_information()
            return Response({"ok": True, "bybit": info})
        except InvalidRequestError as e:
            return Response({"ok": False, "error": str(e)}, status=400)

class CredentialSaveView(APIView):
    def post(self, request):
        s = ApiCredentialSaveSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        cred = s.save()
        return Response({"ok": True, "id": cred.id})

class OnboardingStateView(APIView):
    def get(self, request):
        has_testnet = ApiCredential.objects.filter(user=request.user, is_testnet=True).exists()
        return Response({"has_testnet_credentials": has_testnet})
