from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.accounts.models import Membership
from apps.core.views import TenantRequiredMixin
from apps.verticals.registry import VerticalRequiredMixin

from .forms import ClinicalRecordForm, SessionNoteForm
from .models import ClinicalRecord, SessionNote


class PsychologyVerticalMixin(LoginRequiredMixin, TenantRequiredMixin, VerticalRequiredMixin):
    vertical_key = "psicologia"


class ClinicalRecordAccessRequiredMixin:
    """Além do módulo estar habilitado (PsychologyVerticalMixin), exige que
    o usuário logado tenha acesso a ESTE prontuário específico. Precisa
    vir DEPOIS de PsychologyVerticalMixin na lista de bases da view (não
    antes) — assim o MRO garante que login/tenant/módulo já foram
    checados (e request.user já está resolvido) antes desta checagem
    rodar; ver a ordem em cada view abaixo."""

    def dispatch(self, request, *args, **kwargs):
        self.clinical_record = get_object_or_404(ClinicalRecord, pk=kwargs["record_pk"])
        if not self.clinical_record.user_has_access(request.user):
            raise PermissionDenied("Você não tem acesso a este prontuário.")
        return super().dispatch(request, *args, **kwargs)


def _is_tenant_admin(request):
    return Membership.objects.filter(
        user=request.user,
        tenant=request.tenant,
        role=Membership.Role.ADMIN_EMPRESA,
        is_active=True,
    ).exists()


class ClinicalRecordListView(PsychologyVerticalMixin, ListView):
    """Só mostra os prontuários que o usuário logado tem acesso — ao
    contrário do Odontologia, isso NÃO é uma lista de todos os clientes:
    listar quem está em terapia já seria, por si só, uma violação."""

    template_name = "verticals/psychology/clinical_record_list.html"
    context_object_name = "clinical_records"

    def get_queryset(self):
        user = self.request.user
        return (
            ClinicalRecord.objects.select_related("client", "responsible_professional")
            .filter(Q(responsible_professional__user=user) | Q(authorized_users=user))
            .distinct()
        )


class ClinicalRecordCreateView(PsychologyVerticalMixin, CreateView):
    model = ClinicalRecord
    form_class = ClinicalRecordForm
    template_name = "verticals/psychology/clinical_record_form.html"
    success_url = reverse_lazy("psychology:clinical_record_list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class ClinicalRecordDetailView(PsychologyVerticalMixin, ClinicalRecordAccessRequiredMixin, DetailView):
    model = ClinicalRecord
    pk_url_kwarg = "record_pk"
    template_name = "verticals/psychology/clinical_record_detail.html"
    context_object_name = "clinical_record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["session_notes"] = self.object.session_notes.all()
        ctx["note_form"] = SessionNoteForm()
        ctx["is_tenant_admin"] = _is_tenant_admin(self.request)
        granted_ids = set(self.object.authorized_users.values_list("pk", flat=True))
        ctx["grantable_memberships"] = (
            Membership.objects.filter(tenant=self.request.tenant, is_active=True)
            .exclude(user_id=self.object.responsible_professional.user_id)
            .exclude(user_id__in=granted_ids)
            .select_related("user")
        )
        return ctx


class SessionNoteCreateView(PsychologyVerticalMixin, ClinicalRecordAccessRequiredMixin, View):
    def post(self, request, record_pk):
        form = SessionNoteForm(request.POST)
        if form.is_valid():
            form.instance.tenant = request.tenant
            form.instance.clinical_record = self.clinical_record
            form.instance.created_by = request.user
            form.save()
        return redirect("psychology:clinical_record_detail", record_pk=record_pk)


class ClinicalRecordGrantAccessView(PsychologyVerticalMixin, View):
    """Conceder acesso é uma ação administrativa distinta de LER o
    conteúdo — por isso não usa ClinicalRecordAccessRequiredMixin (senão
    quem ainda não tem acesso nunca conseguiria chegar a receber a
    concessão). Só quem já tem acesso ou é admin_empresa pode conceder."""

    def post(self, request, record_pk):
        clinical_record = get_object_or_404(ClinicalRecord, pk=record_pk)
        if not (clinical_record.user_has_access(request.user) or _is_tenant_admin(request)):
            raise PermissionDenied("Você não pode conceder acesso a este prontuário.")

        target_membership = get_object_or_404(
            Membership, tenant=request.tenant, user_id=request.POST.get("user_id"), is_active=True
        )
        clinical_record.authorized_users.add(target_membership.user)
        messages.success(request, "Acesso concedido.")
        return redirect("psychology:clinical_record_detail", record_pk=record_pk)


class ClinicalRecordRevokeAccessView(PsychologyVerticalMixin, View):
    def post(self, request, record_pk, user_pk):
        clinical_record = get_object_or_404(ClinicalRecord, pk=record_pk)
        if not (clinical_record.user_has_access(request.user) or _is_tenant_admin(request)):
            raise PermissionDenied("Você não pode revogar acesso a este prontuário.")
        clinical_record.authorized_users.remove(user_pk)
        messages.success(request, "Acesso revogado.")
        return redirect("psychology:clinical_record_detail", record_pk=record_pk)
