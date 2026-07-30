from django.utils import timezone

from apps.accounts.models import Membership
from apps.scheduling.models import Appointment
from apps.verticals.registry import get_active_verticals_detail

from .navigation import build_nav


def shell(request):
    """Dados que o layout base (templates/layouts/app_shell.html) precisa em
    toda página autenticada: papel do usuário na empresa atual, o
    profissional vinculado a ele (se houver, usado pelo item de menu
    "Calendário") e uma lista curta de atendimentos de hoje para o sino de
    notificações. Tudo real, sem placeholder — se não houver dado, a seção
    correspondente aparece vazia em vez de inventar conteúdo."""

    tenant = getattr(request, "tenant", None)
    user = getattr(request, "user", None)

    if tenant is None or user is None or not user.is_authenticated:
        return {}

    membership = (
        Membership.objects.filter(tenant=tenant, user=user, is_active=True)
        .first()
    )
    has_other_tenants = (
        Membership.objects.filter(user=user, is_active=True).exclude(tenant=tenant).exists()
    )
    professional = getattr(user, "professional_profiles", None)
    current_professional = professional.filter(tenant=tenant).first() if professional else None

    now = timezone.localtime()
    upcoming_appointments = list(
        Appointment.objects.filter(
            tenant=tenant,
            start_at__gte=now,
            start_at__date=now.date(),
            status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
        )
        .select_related("client", "professional")
        .order_by("start_at")[:5]
    )

    nav_sections, active_nav_section = build_nav(
        request, tenant, current_professional, get_active_verticals_detail(tenant)
    )
    search_destinations = [
        {"label": item["label"], "href": item["href"], "section": section["label"]}
        for section in nav_sections
        for item in section["items"]
        if not item["disabled"]
    ]

    return {
        "current_membership": membership,
        "has_other_tenants": has_other_tenants,
        "current_professional": current_professional,
        "upcoming_appointments": upcoming_appointments,
        "nav_sections": nav_sections,
        "active_nav_section": active_nav_section,
        "search_destinations": search_destinations,
    }
