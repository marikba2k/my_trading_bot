from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ApiCredential

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    class Meta:
        model = User
        fields = ("username","email","password")
    def create(self, validated):
        return User.objects.create_user(
            username=validated["username"],
            email=validated.get("email",""),
            password=validated["password"]
        )

class ApiCredentialTestSerializer(serializers.Serializer):
    api_key = serializers.CharField()
    api_secret = serializers.CharField()
    is_testnet = serializers.BooleanField(default=True)

class ApiCredentialSaveSerializer(serializers.ModelSerializer):
    api_secret = serializers.CharField(write_only=True)
    class Meta:
        model = ApiCredential
        fields = ("exchange","is_testnet","api_key","api_secret")
        extra_kwargs = {"exchange": {"default":"bybit"}}
    def create(self, validated):
        user = self.context["request"].user
        cred, _ = ApiCredential.objects.get_or_create(
            user=user, exchange=validated.get("exchange","bybit"),
            is_testnet=validated["is_testnet"],
            defaults={"api_key": validated["api_key"], "api_secret_enc": b""},
        )
        cred.api_key = validated["api_key"]
        cred.set_secret(validated["api_secret"])
        cred.save()
        return cred
