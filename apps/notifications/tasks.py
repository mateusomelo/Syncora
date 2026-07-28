from datetime import timedelta

from celery import shared_task
from django.db.models import Max, Q
from django.utils import timezone

from apps.clients.models import Client
from apps.scheduling.models import Appointment

from .models import NotificationLog
from .services import notify_client

# Estas tasks rodam como jobs de plataforma (Celery beat), fora de qualquer
# request — não existe tenant no contextvar, então usam `all_objects`
# deliberadamente (ver apps/core/models.py) para varrer todas as empresas.
# notify_client()/NotificationLog.objects.create() continuam funcionando
# normalmente porque criar linha não depende de leitura filtrada.


@shared_task
def send_appointment_reminders():
    """Lembra clientes de atendimentos entre 23h e 25h no futuro que ainda
    não receberam lembrete — pensado para rodar a cada hora via Celery beat."""
    window_start = timezone.now() + timedelta(hours=23)
    window_end = timezone.now() + timedelta(hours=25)

    appointments = Appointment.all_objects.filter(
        start_at__gte=window_start,
        start_at__lt=window_end,
        status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
    )

    sent = 0
    for appointment in appointments:
        already_sent = NotificationLog.all_objects.filter(
            appointment=appointment,
            notification_type=NotificationLog.NotificationType.REMINDER,
            status=NotificationLog.Status.SENT,
        ).exists()
        if already_sent:
            continue
        notify_client(
            tenant=appointment.tenant,
            client=appointment.client,
            notification_type=NotificationLog.NotificationType.REMINDER,
            subject="Lembrete de agendamento · Syncora",
            template_name="appointment_reminder",
            context={"appointment": appointment},
            appointment=appointment,
        )
        sent += 1
    return sent


@shared_task
def send_birthday_greetings():
    """Roda uma vez por dia (Celery beat) e cumprimenta clientes cujo
    aniversário é hoje, em qualquer empresa."""
    today = timezone.localdate()
    clients = Client.all_objects.filter(birth_date__month=today.month, birth_date__day=today.day)

    sent = 0
    for client in clients:
        already_sent_today = NotificationLog.all_objects.filter(
            client=client,
            notification_type=NotificationLog.NotificationType.BIRTHDAY,
            created_at__date=today,
        ).exists()
        if already_sent_today:
            continue
        notify_client(
            tenant=client.tenant,
            client=client,
            notification_type=NotificationLog.NotificationType.BIRTHDAY,
            subject="Feliz aniversário! · Syncora",
            template_name="birthday",
            context={"client": client},
        )
        sent += 1
    return sent


@shared_task
def send_return_reminders(days_since_last_visit=45):
    """Avisa clientes que não retornam há `days_since_last_visit` dias e não
    têm nada agendado para o futuro. Roda uma vez por dia (Celery beat)."""
    cutoff = timezone.now() - timedelta(days=days_since_last_visit)

    candidates = (
        Client.all_objects.annotate(
            last_completed=Max(
                "appointments__start_at",
                filter=Q(appointments__status=Appointment.Status.COMPLETED),
            )
        )
        .filter(last_completed__lt=cutoff)
    )

    sent = 0
    for client in candidates:
        has_future = (
            Appointment.all_objects.filter(client=client, start_at__gte=timezone.now())
            .exclude(status=Appointment.Status.CANCELLED)
            .exists()
        )
        if has_future:
            continue

        already_sent_recently = NotificationLog.all_objects.filter(
            client=client,
            notification_type=NotificationLog.NotificationType.RETURN_REMINDER,
            created_at__gte=timezone.now() - timedelta(days=days_since_last_visit),
        ).exists()
        if already_sent_recently:
            continue

        notify_client(
            tenant=client.tenant,
            client=client,
            notification_type=NotificationLog.NotificationType.RETURN_REMINDER,
            subject="Sentimos sua falta! · Syncora",
            template_name="return_reminder",
            context={"client": client},
        )
        sent += 1
    return sent
