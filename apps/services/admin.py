from django.contrib import admin

from .models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant")
    list_filter = ("tenant",)

    def get_queryset(self, request):
        return ServiceCategory.all_objects.all()


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "category", "price", "duration_minutes", "is_active")
    list_filter = ("tenant", "category", "is_active")
    search_fields = ("name",)
    filter_horizontal = ("allowed_professionals",)

    def get_queryset(self, request):
        return Service.all_objects.all()
