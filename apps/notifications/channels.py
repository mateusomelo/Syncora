from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


class NotificationChannel:
    """Interface que qualquer canal de notificação implementa — o ponto de
    extensão para as integrações futuras (WhatsApp, SMS, Telegram)."""

    name = None

    def send(self, *, to, subject, template_name, context):
        raise NotImplementedError


class EmailChannel(NotificationChannel):
    name = "email"

    def send(self, *, to, subject, template_name, context):
        body = render_to_string(f"notifications/{template_name}.txt", context)
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to])


class WhatsAppChannel(NotificationChannel):
    """Stub — integração real (ex.: Meta Cloud API) é trabalho da fase de
    Integrações Futuras. Existe aqui só para o ponto de plugin já estar
    desenhado; chamar .send() hoje sempre falha de propósito."""

    name = "whatsapp"

    def send(self, *, to, subject, template_name, context):
        raise NotImplementedError("Integração com WhatsApp ainda não configurada.")


class SMSChannel(NotificationChannel):
    """Stub — mesma situação do WhatsAppChannel."""

    name = "sms"

    def send(self, *, to, subject, template_name, context):
        raise NotImplementedError("Integração com SMS ainda não configurada.")
