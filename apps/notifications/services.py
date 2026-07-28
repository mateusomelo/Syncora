import logging

from .channels import EmailChannel
from .models import NotificationLog

logger = logging.getLogger("syncora.notifications")


def notify_client(*, tenant, client, notification_type, subject, template_name, context, appointment=None):
    """Envia uma notificação ao cliente e registra o resultado em
    NotificationLog. Hoje só e-mail está de fato integrado (EmailChannel);
    WhatsApp/SMS existem como stubs plugáveis em channels.py, prontos para
    quando as integrações reais forem construídas — sem precisar mudar
    quem chama notify_client."""

    if not client.email:
        _log(tenant, client, appointment, notification_type, NotificationLog.Channel.EMAIL, NotificationLog.Status.SKIPPED, "Cliente sem e-mail cadastrado.")
        return

    try:
        EmailChannel().send(to=client.email, subject=subject, template_name=template_name, context=context)
    except Exception as exc:
        logger.exception("Falha ao enviar notificação %s para %s", notification_type, client.email)
        _log(tenant, client, appointment, notification_type, NotificationLog.Channel.EMAIL, NotificationLog.Status.FAILED, str(exc))
        return

    _log(tenant, client, appointment, notification_type, NotificationLog.Channel.EMAIL, NotificationLog.Status.SENT, "")


def _log(tenant, client, appointment, notification_type, channel, status, error_message):
    NotificationLog.objects.create(
        tenant=tenant,
        client=client,
        appointment=appointment,
        notification_type=notification_type,
        channel=channel,
        status=status,
        error_message=error_message,
    )
