import requests
from django.utils import timezone

from .models import CalendarConnection, ExternalEventMapping


class ProviderAPIError(Exception):
    pass


def _authorized_headers(connection):
    return {"Authorization": f"Bearer {connection.access_token}"}


def pull_events(connection, http=requests):
    """Busca eventos do provedor externo e atualiza ExternalEventMapping.

    `http` é injetável de propósito: os testes passam um objeto falso em vez
    de bater na API real do Google/Microsoft (que exige credenciais e
    consentimento reais, impossíveis de automatizar aqui) — isso prova que
    a orquestração (parsing, upsert, respeito ao sync_direction) está
    correta, mesmo sem uma conta de verdade."""

    if connection.sync_direction in (
        CalendarConnection.SyncDirection.OUT_ONLY,
        CalendarConnection.SyncDirection.DISABLED,
    ):
        return 0
    if connection.provider == CalendarConnection.Provider.GOOGLE:
        return _pull_google(connection, http)
    if connection.provider == CalendarConnection.Provider.OUTLOOK:
        return _pull_outlook(connection, http)
    raise ProviderAPIError(f"Provedor {connection.provider} não suporta importação ainda.")


def _pull_google(connection, http):
    response = http.get(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers=_authorized_headers(connection),
        params={
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeMin": timezone.now().isoformat(),
        },
        timeout=10,
    )
    if response.status_code != 200:
        raise ProviderAPIError(f"Google Calendar respondeu {response.status_code}")

    count = 0
    for event in response.json().get("items", []):
        start = event.get("start", {}).get("dateTime")
        end = event.get("end", {}).get("dateTime")
        if not start or not end:
            continue  # evento de dia inteiro (sem hora) — fora de escopo por ora
        ExternalEventMapping.all_objects.update_or_create(
            connection=connection,
            external_event_id=event["id"],
            defaults={
                "tenant": connection.tenant,
                "title": event.get("summary", "(sem título)"),
                "start_at": start,
                "end_at": end,
            },
        )
        count += 1

    connection.last_synced_at = timezone.now()
    connection.save(update_fields=["last_synced_at"])
    return count


def _pull_outlook(connection, http):
    response = http.get(
        "https://graph.microsoft.com/v1.0/me/events",
        headers=_authorized_headers(connection),
        timeout=10,
    )
    if response.status_code != 200:
        raise ProviderAPIError(f"Microsoft Graph respondeu {response.status_code}")

    count = 0
    for event in response.json().get("value", []):
        start = event.get("start", {}).get("dateTime")
        end = event.get("end", {}).get("dateTime")
        if not start or not end:
            continue
        ExternalEventMapping.all_objects.update_or_create(
            connection=connection,
            external_event_id=event["id"],
            defaults={
                "tenant": connection.tenant,
                "title": event.get("subject", "(sem título)"),
                "start_at": start,
                "end_at": end,
            },
        )
        count += 1

    connection.last_synced_at = timezone.now()
    connection.save(update_fields=["last_synced_at"])
    return count


def push_appointment(appointment, http=requests):
    """Cria/atualiza o compromisso nos calendários externos conectados do
    profissional, respeitando sync_direction de cada conexão. Chamado a
    partir do signal em apps/calendar_sync/signals.py."""

    connections = CalendarConnection.objects.filter(
        professional=appointment.professional, is_active=True
    ).exclude(
        sync_direction__in=[
            CalendarConnection.SyncDirection.IN_ONLY,
            CalendarConnection.SyncDirection.DISABLED,
        ]
    )

    pushed = 0
    for connection in connections:
        if connection.provider == CalendarConnection.Provider.GOOGLE:
            _push_google(connection, appointment, http)
            pushed += 1
        elif connection.provider == CalendarConnection.Provider.OUTLOOK:
            _push_outlook(connection, appointment, http)
            pushed += 1
    return pushed


def _event_body(appointment):
    return {
        "summary": f"{appointment.service.name} · {appointment.client.name}",
        "start": {"dateTime": appointment.start_at.isoformat()},
        "end": {"dateTime": appointment.end_at.isoformat()},
    }


def _push_google(connection, appointment, http):
    mapping = ExternalEventMapping.objects.filter(connection=connection, appointment=appointment).first()
    body = _event_body(appointment)

    if mapping:
        response = http.patch(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{mapping.external_event_id}",
            headers=_authorized_headers(connection),
            json=body,
            timeout=10,
        )
    else:
        response = http.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=_authorized_headers(connection),
            json=body,
            timeout=10,
        )
    if response.status_code not in (200, 201):
        raise ProviderAPIError(f"Google Calendar respondeu {response.status_code} ao gravar o evento")

    data = response.json()
    ExternalEventMapping.objects.update_or_create(
        connection=connection,
        appointment=appointment,
        defaults={
            "tenant": appointment.tenant,
            "external_event_id": data["id"],
            "title": body["summary"],
            "start_at": appointment.start_at,
            "end_at": appointment.end_at,
        },
    )


def _push_outlook(connection, appointment, http):
    mapping = ExternalEventMapping.objects.filter(connection=connection, appointment=appointment).first()
    body = {
        "subject": f"{appointment.service.name} · {appointment.client.name}",
        "start": {"dateTime": appointment.start_at.isoformat(), "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": appointment.end_at.isoformat(), "timeZone": "America/Sao_Paulo"},
    }

    if mapping:
        response = http.patch(
            f"https://graph.microsoft.com/v1.0/me/events/{mapping.external_event_id}",
            headers=_authorized_headers(connection),
            json=body,
            timeout=10,
        )
    else:
        response = http.post(
            "https://graph.microsoft.com/v1.0/me/events",
            headers=_authorized_headers(connection),
            json=body,
            timeout=10,
        )
    if response.status_code not in (200, 201):
        raise ProviderAPIError(f"Microsoft Graph respondeu {response.status_code} ao gravar o evento")

    data = response.json()
    ExternalEventMapping.objects.update_or_create(
        connection=connection,
        appointment=appointment,
        defaults={
            "tenant": appointment.tenant,
            "external_event_id": data["id"],
            "title": body["subject"],
            "start_at": appointment.start_at,
            "end_at": appointment.end_at,
        },
    )
