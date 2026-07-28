from django.contrib import admin

from .models import Commission, Expense, Revenue


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ("received_at", "description", "amount", "payment_method", "tenant")
    list_filter = ("tenant", "payment_method")

    def get_queryset(self, request):
        return Revenue.all_objects.all()


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("due_date", "category", "amount", "paid_at", "tenant")
    list_filter = ("tenant", "category")

    def get_queryset(self, request):
        return Expense.all_objects.all()


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ("professional", "appointment", "amount", "percentage", "paid", "tenant")
    list_filter = ("tenant", "paid")

    def get_queryset(self, request):
        return Commission.all_objects.all()
