from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.views import HtmxTemplateMixin, TenantRequiredMixin

from .forms import ClientDocumentForm, ClientForm
from .models import Client


class ClientListView(LoginRequiredMixin, TenantRequiredMixin, HtmxTemplateMixin, ListView):
    template_name = "clients/client_list.html"
    partial_template_name = "clients/_client_table.html"
    context_object_name = "clients"
    paginate_by = 20

    def get_queryset(self):
        qs = Client.objects.all()
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(phone__icontains=query)
                | Q(email__icontains=query)
            )
        return qs


class ClientCreateView(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, TenantRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:list")


class ClientDetailView(LoginRequiredMixin, TenantRequiredMixin, DetailView):
    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["document_form"] = ClientDocumentForm()
        return ctx


class ClientDocumentCreateView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        form = ClientDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.tenant = request.tenant
            document.client = client
            document.save()
        return redirect("clients:detail", pk=client.pk)


class ClientDeleteView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        client.delete()  # soft delete (SoftDeleteModel.delete)
        if request.htmx:
            return HttpResponse(status=200)
        return redirect("clients:list")
