import logging

from celery import shared_task

from .models import CalendarConnection
from .services import ProviderAPIError, pull_events

logger = logging.getLogger("syncora.calendar_sync")


@shared_task
def sync_all_calendars():
    """Roda periodicamente (Celery beat) puxando eventos de todas as
    conexões ativas, em todas as empresas — por isso usa `all_objects`
    (ver apps/core/models.py: fora de uma request não existe tenant no
    contextvar)."""

    connections = CalendarConnection.all_objects.filter(is_active=True).exclude(
        sync_direction=CalendarConnection.SyncDirection.OUT_ONLY
    ).exclude(sync_direction=CalendarConnection.SyncDirection.DISABLED)

    synced, failed = 0, 0
    for connection in connections:
        try:
            pull_events(connection)
            synced += 1
        except ProviderAPIError:
            logger.exception(
                "Falha ao importar eventos de %s (%s)", connection.professional, connection.provider
            )
            failed += 1
    return {"synced": synced, "failed": failed}
