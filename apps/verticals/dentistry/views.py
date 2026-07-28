from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from apps.clients.models import Client
from apps.core.views import TenantRequiredMixin
from apps.verticals.registry import VerticalRequiredMixin

from .forms import (
    AnamnesisForm,
    BudgetForm,
    MedicalCertificateForm,
    PrescriptionForm,
    ToothConditionFormSet,
    TreatmentForm,
)
from .models import (
    Anamnesis,
    Budget,
    Installment,
    MedicalCertificate,
    Odontogram,
    Prescription,
    Treatment,
)
from .services import generate_installments


class DentistryVerticalMixin(LoginRequiredMixin, TenantRequiredMixin, VerticalRequiredMixin):
    vertical_key = "odontologia"


class PatientListView(DentistryVerticalMixin, ListView):
    template_name = "verticals/dentistry/patient_list.html"
    context_object_name = "clients"

    def get_queryset(self):
        return Client.objects.all()


class BudgetListView(DentistryVerticalMixin, ListView):
    template_name = "verticals/dentistry/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        return Budget.objects.select_related("client").all()


class ClientDentalRecordView(DentistryVerticalMixin, TemplateView):
    """Prontuário odontológico do cliente: anamnese, odontograma,
    tratamentos, receitas, atestados e orçamentos, tudo em uma tela."""

    template_name = "verticals/dentistry/dental_record.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client = get_object_or_404(Client, pk=self.kwargs["client_pk"])
        odontogram = Odontogram.objects.filter(client=client).first()
        ctx.update(
            {
                "client": client,
                "anamnesis": Anamnesis.objects.filter(client=client).first(),
                "odontogram": odontogram,
                "teeth": odontogram.teeth.all() if odontogram else [],
                "treatments": Treatment.objects.filter(client=client),
                "prescriptions": Prescription.objects.filter(client=client),
                "certificates": MedicalCertificate.objects.filter(client=client),
                "budgets": Budget.objects.filter(client=client).prefetch_related("installments"),
            }
        )
        return ctx


class OdontogramCreateView(DentistryVerticalMixin, View):
    def post(self, request, client_pk):
        client = get_object_or_404(Client, pk=client_pk)
        if not Odontogram.objects.filter(client=client).exists():
            Odontogram.create_for_client(client)
        return redirect("dentistry:dental_record", client_pk=client_pk)


class OdontogramUpdateView(DentistryVerticalMixin, View):
    def post(self, request, client_pk):
        odontogram = get_object_or_404(Odontogram, client_id=client_pk)
        formset = ToothConditionFormSet(request.POST, queryset=odontogram.teeth.all())
        if formset.is_valid():
            formset.save()
            messages.success(request, "Odontograma atualizado.")
        return redirect("dentistry:dental_record", client_pk=client_pk)


class AnamnesisEditView(DentistryVerticalMixin, View):
    def get(self, request, client_pk):
        client = get_object_or_404(Client, pk=client_pk)
        instance = Anamnesis.objects.filter(client=client).first()
        form = AnamnesisForm(instance=instance)
        return render(
            request, "verticals/dentistry/anamnesis_form.html", {"form": form, "client": client}
        )

    def post(self, request, client_pk):
        client = get_object_or_404(Client, pk=client_pk)
        instance = Anamnesis.objects.filter(client=client).first()
        form = AnamnesisForm(request.POST, instance=instance)
        if form.is_valid():
            form.instance.tenant = request.tenant
            form.instance.client = client
            form.save()
            return redirect("dentistry:dental_record", client_pk=client_pk)
        return render(
            request, "verticals/dentistry/anamnesis_form.html", {"form": form, "client": client}
        )


class _ClientScopedCreateView(DentistryVerticalMixin, CreateView):
    template_name = "verticals/dentistry/simple_form.html"
    title = ""

    def dispatch(self, request, *args, **kwargs):
        self.client = get_object_or_404(Client, pk=kwargs["client_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        form.instance.client = self.client
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dentistry:dental_record", args=[self.client.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.title
        ctx["client"] = self.client
        return ctx


class TreatmentCreateView(_ClientScopedCreateView):
    model = Treatment
    form_class = TreatmentForm
    title = "Novo tratamento"


class PrescriptionCreateView(_ClientScopedCreateView):
    model = Prescription
    form_class = PrescriptionForm
    title = "Nova receita"


class MedicalCertificateCreateView(_ClientScopedCreateView):
    model = MedicalCertificate
    form_class = MedicalCertificateForm
    title = "Novo atestado"


class BudgetCreateView(_ClientScopedCreateView):
    model = Budget
    form_class = BudgetForm
    title = "Novo orçamento"

    def form_valid(self, form):
        response = super().form_valid(form)
        generate_installments(self.object)
        return response


class InstallmentMarkPaidView(DentistryVerticalMixin, View):
    def post(self, request, client_pk, pk):
        installment = get_object_or_404(Installment, pk=pk, budget__client_id=client_pk)
        installment.paid_at = timezone.localdate()
        installment.save(update_fields=["paid_at"])
        return redirect("dentistry:dental_record", client_pk=client_pk)
