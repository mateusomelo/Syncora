import calendar
from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.views import TenantRequiredMixin
from apps.finance.models import Revenue
from apps.scheduling.models import Appointment
from apps.staff.models import Professional


class DashboardView(LoginRequiredMixin, TenantRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month_start = today.replace(day=1)
        # "Profissional mais ocupado" e "serviços mais usados" olham o mês
        # inteiro (inclui agendamentos futuros já marcados dentro do mês),
        # não só até hoje — reflete a agenda do mês, não só o já realizado.
        month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        day_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        day_end = day_start + timedelta(days=1)

        today_appointments = Appointment.objects.filter(start_at__gte=day_start, start_at__lt=day_end)
        month_appointments = Appointment.objects.filter(
            start_at__date__gte=month_start, start_at__date__lte=month_end
        ).exclude(status=Appointment.Status.CANCELLED)

        busiest = (
            month_appointments.values("professional__name")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
        )

        top_services = list(
            month_appointments.values("service__name").annotate(total=Count("id")).order_by("-total")[:5]
        )
        max_service_total = top_services[0]["total"] if top_services else 0

        revenue_today = (
            Revenue.objects.filter(received_at__date=today).aggregate(total=Sum("amount"))["total"] or 0
        )
        revenue_month = (
            Revenue.objects.filter(received_at__date__gte=month_start, received_at__date__lte=today).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        ctx.update(
            {
                "today": today,
                "today_count": today_appointments.exclude(status=Appointment.Status.CANCELLED).count(),
                "waiting_count": today_appointments.filter(
                    status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]
                ).count(),
                "completed_count": today_appointments.filter(status=Appointment.Status.COMPLETED).count(),
                "cancelled_today": today_appointments.filter(status=Appointment.Status.CANCELLED).count(),
                "revenue_today": revenue_today,
                "revenue_month": revenue_month,
                "busiest_professional": busiest,
                "top_services": top_services,
                "max_service_total": max_service_total,
                "today_agenda": today_appointments.exclude(status=Appointment.Status.CANCELLED)
                .select_related("client", "professional", "service")
                .order_by("start_at"),
                "active_professionals_count": Professional.objects.filter(
                    status=Professional.Status.ACTIVE
                ).count(),
            }
        )
        return ctx
