from django.contrib import admin

from .models import CashMovement, CashRegisterSession, ClientPackage, Package, Product


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "session_count", "price", "is_active", "tenant")
    list_filter = ("tenant", "is_active")

    def get_queryset(self, request):
        return Package.all_objects.all()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock_quantity", "is_active", "tenant")
    list_filter = ("tenant", "is_active")

    def get_queryset(self, request):
        return Product.all_objects.all()


@admin.register(ClientPackage)
class ClientPackageAdmin(admin.ModelAdmin):
    list_display = ("client", "package", "sessions_remaining", "purchased_at", "tenant")
    list_filter = ("tenant",)

    def get_queryset(self, request):
        return ClientPackage.all_objects.all()


class CashMovementInline(admin.TabularInline):
    model = CashMovement
    extra = 0


@admin.register(CashRegisterSession)
class CashRegisterSessionAdmin(admin.ModelAdmin):
    list_display = ("opened_at", "opened_by", "status", "opening_amount", "closing_amount", "tenant")
    list_filter = ("tenant", "status")
    inlines = [CashMovementInline]

    def get_queryset(self, request):
        return CashRegisterSession.all_objects.all()
