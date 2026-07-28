from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet():
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode())


class EncryptedTextField(models.TextField):
    """Criptografa o valor em repouso (Fernet/AES) — usado para tokens OAuth
    de terceiros (Google, Outlook), que nunca devem ficar em texto puro no
    banco. A chave vem de settings.FIELD_ENCRYPTION_KEY (variável de
    ambiente própria, não a mesma coisa que SECRET_KEY)."""

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        return _fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return ""
