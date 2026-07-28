from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.views import HtmxTemplateMixin, TenantRequiredMixin

from .forms import ServiceForm
from .models import Service


class ServiceListView(LoginRequiredMixin, TenantRequiredMixin, HtmxTemplateMixin, ListView):
    template_name = "services/service_list.html"
    partial_template_name = "services/_service_table.html"
    context_object_name = "services"
    paginate_by = 20

    def get_queryset(self):
        qs = Service.objects.select_related("category").all()
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(category__name__icontains=query))
        return qs


class ServiceCreateView(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "services/service_form.html"
    success_url = reverse_lazy("services:list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class ServiceUpdateView(LoginRequiredMixin, TenantRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "services/service_form.html"
    success_url = reverse_lazy("services:list")


class ServiceDetailView(LoginRequiredMixin, TenantRequiredMixin, DetailView):
    model = Service
    template_name = "services/service_detail.html"
    context_object_name = "service"


class ServiceDeleteView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        service.delete()
        if request.htmx:
            return HttpResponse(status=200)
        return redirect("services:list")
