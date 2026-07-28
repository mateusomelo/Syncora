import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.scheduling.models import Appointment

from .models import CalendarConnection
from .services import ProviderAPIError, push_appointment

logger = logging.getLogger("syncora.calendar_sync")


@receiver(post_save, sender=Appointment)
def push_to_external_calendars(sender, instance, created, **kwargs):
    # Cancelamento/remoção do evento externo fica para uma iteração futura
    # desta mesma fase — por ora só empurramos criação/atualização.
    if instance.status == Appointment.Status.CANCELLED:
        return

    has_syncable_connection = (
        CalendarConnection.objects.filter(professional=instance.professional, is_active=True)
        .exclude(
            sync_direction__in=[
                CalendarConnection.SyncDirection.IN_ONLY,
                CalendarConnection.SyncDirection.DISABLED,
            ]
        )
        .exists()
    )
    if not has_syncable_connection:
        return

    try:
        push_appointment(instance)
    except ProviderAPIError:
        logger.exception(
            "Falha ao sincronizar agendamento %s com calendário externo", instance.pk
        )
