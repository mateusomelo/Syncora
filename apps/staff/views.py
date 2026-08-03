from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.views import HtmxTemplateMixin, TenantRequiredMixin

from .forms import ProfessionalForm, WorkingHoursForm
from .models import Professional


class ProfessionalListView(LoginRequiredMixin, TenantRequiredMixin, HtmxTemplateMixin, ListView):
    template_name = "staff/professional_list.html"
    partial_template_name = "staff/_professional_table.html"
    context_object_name = "professionals"
    paginate_by = 20

    def get_queryset(self):
        qs = Professional.objects.all()
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(specialties__icontains=query))
        return qs


class ProfessionalCreateView(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = Professional
    form_class = ProfessionalForm
    template_name = "staff/professional_form.html"
    success_url = reverse_lazy("staff:list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class ProfessionalUpdateView(LoginRequiredMixin, TenantRequiredMixin, UpdateView):
    model = Professional
    form_class = ProfessionalForm
    template_name = "staff/professional_form.html"
    success_url = reverse_lazy("staff:list")


class ProfessionalDetailView(LoginRequiredMixin, TenantRequiredMixin, DetailView):
    model = Professional
    template_name = "staff/professional_detail.html"
    context_object_name = "professional"


class ProfessionalDeleteView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        professional = get_object_or_404(Professional, pk=pk)
        professional.delete()
        if request.htmx:
            return HttpResponse(status=200)
        return redirect("staff:list")


class WorkingHoursUpdateView(LoginRequiredMixin, TenantRequiredMixin, View):
    template_name = "staff/working_hours_form.html"

    def get(self, request, pk):
        professional = get_object_or_404(Professional, pk=pk)
        form = WorkingHoursForm(professional=professional)
        return render(request, self.template_name, {"professional": professional, "form": form})

    def post(self, request, pk):
        professional = get_object_or_404(Professional, pk=pk)
        form = WorkingHoursForm(request.POST, professional=professional)
        if form.is_valid():
            form.save()
            messages.success(request, "Horário de trabalho atualizado.")
            return redirect("staff:detail", pk=pk)
        return render(request, self.template_name, {"professional": professional, "form": form})
