from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.views import TenantRequiredMixin
from apps.finance.models import Commission, Expense, Revenue
from apps.scheduling.models import Appointment

from .exporters import export_excel, export_pdf


class ReportsHomeView(LoginRequiredMixin, TenantRequiredMixin, TemplateView):
    template_name = "reports/home.html"


def _date_range_from_request(request):
    today = timezone.localdate()
    start = date.fromisoformat(request.GET.get("start") or today.replace(day=1).isoformat())
    end = date.fromisoformat(request.GET.get("end") or today.isoformat())
    return start, end


class AppointmentsReportView(LoginRequiredMixin, TenantRequiredMixin, TemplateView):
    template_name = "reports/appointments.html"

    def get(self, request, *args, **kwargs):
        start, end = _date_range_from_request(request)
        appointments = (
            Appointment.objects.select_related("client", "professional", "service")
            .filter(start_at__date__gte=start, start_at__date__lte=end)
            .order_by("start_at")
        )
        return self._respond(request, start, end, appointments)

    def _respond(self, request, start, end, appointments):
        headers = ["Data", "Cliente", "Profissional", "Serviço", "Status", "Motivo cancelamento"]
        rows = [
            [
                timezone.localtime(a.start_at).strftime("%d/%m/%Y %H:%M"),
                a.client.name,
                a.professional.name,
                a.service.name,
                a.get_status_display(),
                a.cancellation_reason,
            ]
            for a in appointments
        ]

        export = request.GET.get("export")
        if export == "xlsx":
            return export_excel(f"agendamentos_{start}_{end}", headers, rows)
        if export == "pdf":
            return export_pdf(
                f"agendamentos_{start}_{end}",
                f"Relatório de Agendamentos ({start:%d/%m/%Y} a {end:%d/%m/%Y})",
                headers,
                rows,
            )

        return self.render_to_response(
            {
                "start": start,
                "end": end,
                "appointments": appointments,
                "cancelled_count": appointments.filter(status=Appointment.Status.CANCELLED).count(),
            }
        )


class FinancialReportView(LoginRequiredMixin, TenantRequiredMixin, TemplateView):
    template_name = "reports/financial.html"

    def get(self, request, *args, **kwargs):
        start, end = _date_range_from_request(request)
        revenues = Revenue.objects.filter(received_at__date__gte=start, received_at__date__lte=end)
        expenses = Expense.objects.filter(due_date__gte=start, due_date__lte=end)

        export = request.GET.get("export")
        if export in ("xlsx", "pdf"):
            headers = ["Tipo", "Data", "Descrição", "Valor"]
            rows = [
                ["Receita", timezone.localtime(r.received_at).strftime("%d/%m/%Y"), r.description, r.amount]
                for r in revenues
            ] + [["Despesa", e.due_date.strftime("%d/%m/%Y"), e.category, -e.amount] for e in expenses]
            if export == "xlsx":
                return export_excel(f"financeiro_{start}_{end}", headers, rows)
            return export_pdf(
                f"financeiro_{start}_{end}",
                f"Relatório Financeiro ({start:%d/%m/%Y} a {end:%d/%m/%Y})",
                headers,
                rows,
            )

        total_revenue = revenues.aggregate(total=Sum("amount"))["total"] or 0
        total_expense = expenses.aggregate(total=Sum("amount"))["total"] or 0
        return self.render_to_response(
            {
                "start": start,
                "end": end,
                "revenues": revenues,
                "expenses": expenses,
                "total_revenue": total_revenue,
                "total_expense": total_expense,
                "net": total_revenue - total_expense,
            }
        )


class CommissionsReportView(LoginRequiredMixin, TenantRequiredMixin, TemplateView):
    template_name = "reports/commissions.html"

    def get(self, request, *args, **kwargs):
        start, end = _date_range_from_request(request)
        commissions = Commission.objects.select_related("professional", "appointment").filter(
            appointment__start_at__date__gte=start, appointment__start_at__date__lte=end
        )

        export = request.GET.get("export")
        if export in ("xlsx", "pdf"):
            headers = ["Profissional", "Atendimento", "Valor", "%", "Paga"]
            rows = [
                [
                    c.professional.name,
                    timezone.localtime(c.appointment.start_at).strftime("%d/%m/%Y"),
                    c.amount,
                    c.percentage,
                    "Sim" if c.paid else "Não",
                ]
                for c in commissions
            ]
            if export == "xlsx":
                return export_excel(f"comissoes_{start}_{end}", headers, rows)
            return export_pdf(
                f"comissoes_{start}_{end}",
                f"Relatório de Comissões ({start:%d/%m/%Y} a {end:%d/%m/%Y})",
                headers,
                rows,
            )

        total = commissions.aggregate(total=Sum("amount"))["total"] or 0
        return self.render_to_response(
            {"start": start, "end": end, "commissions": commissions, "total": total}
        )
