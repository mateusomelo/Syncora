from django.contrib import admin

from .models import Client, ClientDocument


class ClientDocumentInline(admin.TabularInline):
    model = ClientDocument
    extra = 0


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "phone", "email", "created_at")
    list_filter = ("tenant",)
    search_fields = ("name", "phone", "email")
    inlines = [ClientDocumentInline]

    def get_queryset(self, request):
        # Client.objects (TenantManager) filtra pelo contextvar de tenant, que
        # é None no domínio administrativo — o admin precisa do acesso
        # cross-tenant explícito.
        return Client.all_objects.all()
