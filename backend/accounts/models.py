from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet
import base64, os

def _get_fernet():
    key = os.getenv("FERNET_KEY")
    if not key:
        # dev fallback: derive from SECRET_KEY (ok for dev only)
        key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32])
    return Fernet(key)

class ApiCredential(models.Model):
    EXCHANGE_CHOICES = (("bybit","Bybit"),)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exchange = models.CharField(max_length=32, choices=EXCHANGE_CHOICES, default="bybit")
    is_testnet = models.BooleanField(default=True)
    api_key = models.CharField(max_length=128)
    api_secret_enc = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    def set_secret(self, raw: str):
        f = _get_fernet()
        self.api_secret_enc = f.encrypt(raw.encode())

    def get_secret(self) -> str:
        f = _get_fernet()
        return f.decrypt(self.api_secret_enc).decode()

    class Meta:
        unique_together = ("user","exchange","is_testnet")


