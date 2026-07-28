from datetime import date as date_cls
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView, UpdateView

from apps.calendar_sync.models import ExternalEventMapping
from apps.clients.models import Client
from apps.core.views import TenantRequiredMixin
from apps.services.models import Service
from apps.staff.models import Professional

from .forms import AppointmentForm, CancelAppointmentForm
from .models import Appointment, WaitList
from .services import check_conflicts


def _parse_date(value):
    try:
        return date_cls.fromisoformat(value)
    except (TypeError, ValueError):
        return timezone.localdate()


class CalendarDayView(LoginRequiredMixin, TenantRequiredMixin, TemplateView):
    template_name = "scheduling/calendar_day.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        day = _parse_date(self.request.GET.get("date"))
        start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        end = start + timedelta(days=1)
        origin_filter = self.request.GET.get("origin", "all")

        appointments = []
        if origin_filter in ("all", "syncora"):
            appointments = list(
                Appointment.objects.select_related("client", "professional", "service", "room")
                .filter(start_at__gte=start, start_at__lt=end)
                .exclude(status=Appointment.Status.CANCELLED)
            )

        external_events = []
        if origin_filter in ("all", "google", "outlook", "apple"):
            external_qs = ExternalEventMapping.objects.select_related(
                "connection__professional"
            ).filter(start_at__gte=start, start_at__lt=end)
            if origin_filter != "all":
                external_qs = external_qs.filter(connection__provider=origin_filter)
            external_events = list(external_qs)

        columns = []
        for professional in Professional.objects.filter(status=Professional.Status.ACTIVE):
            columns.append(
                {
                    "professional": professional,
                    "appointments": [
                        a for a in appointments if a.professional_id == professional.id
                    ],
                    "external_events": [
                        e for e in external_events if e.connection.professional_id == professional.id
                    ],
                }
            )

        ctx["day"] = day
        ctx["previous_day"] = day - timedelta(days=1)
        ctx["next_day"] = day + timedelta(days=1)
        ctx["columns"] = columns
        ctx["origin_filter"] = origin_filter
        ctx["origins"] = [
            ("all", "Todos"),
            ("syncora", "Somente Syncora"),
            ("google", "Somente Google"),
            ("outlook", "Somente Outlook"),
            ("apple", "Somente Apple"),
        ]
        return ctx


class AppointmentCreateView(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = "scheduling/appointment_form.html"

    def get_initial(self):
        initial = super().get_initial()
        date_param = self.request.GET.get("date")
        if date_param:
            initial["start_at"] = date_param
        return initial

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        response = super().form_valid(form)
        messages.success(self.request, "Agendamento criado.")
        return response

    def get_success_url(self):
        return f"{reverse('scheduling:calendar_day')}?date={self.object.start_at.date().isoformat()}"


class AppointmentUpdateView(LoginRequiredMixin, TenantRequiredMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = "scheduling/appointment_form.html"

    def get_success_url(self):
        return f"{reverse('scheduling:calendar_day')}?date={self.object.start_at.date().isoformat()}"


class AppointmentDetailView(LoginRequiredMixin, TenantRequiredMixin, DetailView):
    model = Appointment
    template_name = "scheduling/appointment_detail.html"
    context_object_name = "appointment"


class AppointmentConfirmView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save(update_fields=["status"])
        messages.success(request, "Agendamento confirmado.")
        return redirect("scheduling:appointment_detail", pk=pk)


class AppointmentCheckInView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = Appointment.Status.CHECKED_IN
        appointment.save(update_fields=["status"])
        messages.success(request, "Check-in realizado.")
        return redirect("scheduling:appointment_detail", pk=pk)


class AppointmentCompleteView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = Appointment.Status.COMPLETED
        appointment.save(update_fields=["status"])
        messages.success(request, "Atendimento concluído.")
        return redirect("scheduling:appointment_detail", pk=pk)


class AppointmentCancelView(LoginRequiredMixin, TenantRequiredMixin, FormView):
    form_class = CancelAppointmentForm
    template_name = "scheduling/appointment_cancel.html"

    def dispatch(self, request, *args, **kwargs):
        self.appointment = get_object_or_404(Appointment, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["appointment"] = self.appointment
        return ctx

    def form_valid(self, form):
        self.appointment.status = Appointment.Status.CANCELLED
        self.appointment.cancellation_reason = form.cleaned_data["reason"]
        self.appointment.save(update_fields=["status", "cancellation_reason"])
        messages.success(self.request, "Agendamento cancelado.")
        return redirect("scheduling:waitlist_matches", pk=self.appointment.pk)


class WaitListMatchesView(LoginRequiredMixin, TenantRequiredMixin, DetailView):
    """Depois de um cancelamento, mostra os clientes da lista de espera
    compatíveis com o horário liberado (mesmo serviço; mesmo profissional
    se a entrada pedir um específico) para preencher com um clique."""

    model = Appointment
    template_name = "scheduling/waitlist_matches.html"
    context_object_name = "appointment"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        appointment = self.object
        ctx["matches"] = WaitList.objects.filter(
            service=appointment.service, status=WaitList.Status.WAITING
        ).filter(Q(professional=appointment.professional) | Q(professional__isnull=True))
        return ctx


class WaitListListView(LoginRequiredMixin, TenantRequiredMixin, ListView):
    template_name = "scheduling/waitlist_list.html"
    context_object_name = "entries"

    def get_queryset(self):
        return WaitList.objects.filter(status=WaitList.Status.WAITING).select_related(
            "client", "service", "professional"
        )


class WaitListCreateView(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = WaitList
    fields = ["client", "service", "professional", "desired_date", "priority"]
    template_name = "scheduling/waitlist_form.html"
    success_url = reverse_lazy("scheduling:waitlist_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["client"].queryset = Client.objects.all()
        form.fields["service"].queryset = Service.objects.all()
        form.fields["professional"].queryset = Professional.objects.all()
        form.fields["professional"].required = False
        return form

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class WaitListFulfillView(LoginRequiredMixin, TenantRequiredMixin, View):
    """Preenche o horário liberado por um cancelamento com 1 clique, usando
    profissional/sala/horário do agendamento cancelado."""

    def post(self, request, appointment_pk, waitlist_pk):
        cancelled = get_object_or_404(Appointment, pk=appointment_pk)
        entry = get_object_or_404(WaitList, pk=waitlist_pk, status=WaitList.Status.WAITING)

        conflicts = check_conflicts(
            professional=cancelled.professional,
            start_at=cancelled.start_at,
            end_at=cancelled.end_at,
            room=cancelled.room,
        )
        if conflicts:
            messages.error(request, "Não foi possível preencher: " + " ".join(conflicts))
            return redirect("scheduling:waitlist_matches", pk=cancelled.pk)

        new_appointment = Appointment.objects.create(
            tenant=request.tenant,
            client=entry.client,
            professional=cancelled.professional,
            service=entry.service,
            room=cancelled.room,
            start_at=cancelled.start_at,
            end_at=cancelled.end_at,
            status=Appointment.Status.CONFIRMED,
        )
        entry.status = WaitList.Status.FULFILLED
        entry.save(update_fields=["status"])
        messages.success(request, f"Horário preenchido com {entry.client.name}.")
        return redirect("scheduling:appointment_detail", pk=new_appointment.pk)
