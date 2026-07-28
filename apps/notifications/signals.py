from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.scheduling.models import Appointment

from .models import NotificationLog
from .services import notify_client


@receiver(pre_save, sender=Appointment)
def stash_previous_appointment_state(sender, instance, **kwargs):
    """Guarda o status/horário anteriores na própria instância para o
    post_save conseguir detectar cancelamento e remarcação. Usa all_objects
    de propósito: esse signal pode disparar fora de uma request (ex.: uma
    sincronização de calendário externo rodando como job), quando o
    contextvar de tenant não está setado."""

    if not instance.pk:
        instance._previous_status = None
        instance._previous_start_at = None
        return

    previous = Appointment.all_objects.filter(pk=instance.pk).first()
    instance._previous_status = previous.status if previous else None
    instance._previous_start_at = previous.start_at if previous else None


@receiver(post_save, sender=Appointment)
def notify_on_appointment_change(sender, instance, created, **kwargs):
    if created:
        notify_client(
            tenant=instance.tenant,
            client=instance.client,
            notification_type=NotificationLog.NotificationType.CONFIRMATION,
            subject="Agendamento confirmado · Syncora",
            template_name="appointment_confirmation",
            context={"appointment": instance},
            appointment=instance,
        )
        return

    previous_status = getattr(instance, "_previous_status", None)
    previous_start_at = getattr(instance, "_previous_start_at", None)

    if previous_status != Appointment.Status.CANCELLED and instance.status == Appointment.Status.CANCELLED:
        notify_client(
            tenant=instance.tenant,
            client=instance.client,
            notification_type=NotificationLog.NotificationType.CANCELLATION,
            subject="Agendamento cancelado · Syncora",
            template_name="appointment_cancellation",
            context={"appointment": instance},
            appointment=instance,
        )
    elif previous_start_at is not None and previous_start_at != instance.start_at:
        notify_client(
            tenant=instance.tenant,
            client=instance.client,
            notification_type=NotificationLog.NotificationType.RESCHEDULE,
            subject="Agendamento remarcado · Syncora",
            template_name="appointment_reschedule",
            context={"appointment": instance, "previous_start_at": previous_start_at},
            appointment=instance,
        )
