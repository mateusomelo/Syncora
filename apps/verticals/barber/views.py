from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.core.views import TenantRequiredMixin
from apps.verticals.registry import VerticalRequiredMixin

from .forms import PackageForm, ProductForm, SellPackageForm
from .models import CashMovement, CashRegisterSession, ClientPackage, Package, Product


class BarberVerticalMixin(LoginRequiredMixin, TenantRequiredMixin, VerticalRequiredMixin):
    vertical_key = "barbearia"


class PackageListView(BarberVerticalMixin, ListView):
    template_name = "verticals/barber/package_list.html"
    context_object_name = "packages"

    def get_queryset(self):
        return Package.objects.all()


class PackageCreateView(BarberVerticalMixin, CreateView):
    model = Package
    form_class = PackageForm
    template_name = "verticals/barber/package_form.html"
    success_url = reverse_lazy("barber:package_list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class PackageUpdateView(BarberVerticalMixin, UpdateView):
    model = Package
    form_class = PackageForm
    template_name = "verticals/barber/package_form.html"
    success_url = reverse_lazy("barber:package_list")


class ProductListView(BarberVerticalMixin, ListView):
    template_name = "verticals/barber/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        return Product.objects.all()


class ProductCreateView(BarberVerticalMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "verticals/barber/product_form.html"
    success_url = reverse_lazy("barber:product_list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class ProductUpdateView(BarberVerticalMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "verticals/barber/product_form.html"
    success_url = reverse_lazy("barber:product_list")


class ClientPackageListView(BarberVerticalMixin, ListView):
    template_name = "verticals/barber/client_package_list.html"
    context_object_name = "client_packages"

    def get_queryset(self):
        return ClientPackage.objects.select_related("client", "package").all()


class ClientPackageCreateView(BarberVerticalMixin, CreateView):
    model = ClientPackage
    form_class = SellPackageForm
    template_name = "verticals/barber/client_package_form.html"
    success_url = reverse_lazy("barber:client_package_list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class ClientPackageUseSessionView(BarberVerticalMixin, View):
    def post(self, request, pk):
        client_package = get_object_or_404(ClientPackage, pk=pk)
        if client_package.sessions_remaining <= 0:
            messages.error(request, "Esse pacote já não tem sessões restantes.")
        else:
            client_package.sessions_remaining -= 1
            client_package.save(update_fields=["sessions_remaining"])
            messages.success(request, f"Sessão usada. Restam {client_package.sessions_remaining}.")
        return redirect("barber:client_package_list")


class CashRegisterView(BarberVerticalMixin, TemplateView):
    template_name = "verticals/barber/cash_register.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session = CashRegisterSession.objects.filter(status=CashRegisterSession.Status.OPEN).first()
        ctx["session"] = session
        if session:
            movements = list(session.movements.all())
            ctx["movements"] = movements
            total_in = sum(m.amount for m in movements if m.type == CashMovement.Type.IN)
            total_out = sum(m.amount for m in movements if m.type == CashMovement.Type.OUT)
            ctx["expected_amount"] = session.opening_amount + total_in - total_out
        return ctx


class CashRegisterOpenView(BarberVerticalMixin, View):
    def post(self, request):
        if CashRegisterSession.objects.filter(status=CashRegisterSession.Status.OPEN).exists():
            messages.error(request, "Já existe um caixa aberto.")
            return redirect("barber:cash_register")
        CashRegisterSession.objects.create(
            tenant=request.tenant,
            opened_by=request.user,
            opening_amount=request.POST.get("opening_amount") or 0,
        )
        return redirect("barber:cash_register")


class CashRegisterCloseView(BarberVerticalMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(
            CashRegisterSession, pk=pk, status=CashRegisterSession.Status.OPEN
        )
        session.closing_amount = request.POST.get("closing_amount") or 0
        session.status = CashRegisterSession.Status.CLOSED
        session.closed_at = timezone.now()
        session.save(update_fields=["closing_amount", "status", "closed_at"])
        return redirect("barber:cash_register")


class CashMovementCreateView(BarberVerticalMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(
            CashRegisterSession, pk=pk, status=CashRegisterSession.Status.OPEN
        )
        CashMovement.objects.create(
            tenant=request.tenant,
            session=session,
            type=request.POST.get("type"),
            amount=request.POST.get("amount") or 0,
            description=request.POST.get("description", ""),
        )
        return redirect("barber:cash_register")
