from django.db import models

from apps.core.models import TenantModel


class NotificationLog(TenantModel):
    class NotificationType(models.TextChoices):
        CONFIRMATION = "confirmation", "Confirmação de agendamento"
        CANCELLATION = "cancellation", "Cancelamento"
        RESCHEDULE = "reschedule", "Remarcação"
        REMINDER = "reminder", "Lembrete"
        BIRTHDAY = "birthday", "Aniversário"
        RETURN_REMINDER = "return_reminder", "Aviso de retorno"

    class Channel(models.TextChoices):
        EMAIL = "email", "E-mail"
        WHATSAPP = "whatsapp", "WhatsApp"
        SMS = "sms", "SMS"

    class Status(models.TextChoices):
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"
        SKIPPED = "skipped", "Ignorado"

    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="notification_logs"
    )
    appointment = models.ForeignKey(
        "scheduling.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
    )
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    error_message = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client", "notification_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} · {self.client} · {self.get_status_display()}"
