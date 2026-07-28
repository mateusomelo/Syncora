from django.contrib import admin

from .models import CustomDomain, Coupon, FeatureFlag, Plan, Tenant, TenantSubscription


class CustomDomainInline(admin.TabularInline):
    model = CustomDomain
    extra = 0


class FeatureFlagInline(admin.TabularInline):
    model = FeatureFlag
    extra = 0


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "subdomain", "plan", "status", "created_at")
    list_filter = ("status", "plan")
    search_fields = ("name", "trade_name", "subdomain", "cnpj")
    inlines = [CustomDomainInline, FeatureFlagInline]


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "price", "max_users", "max_professionals", "is_active")


@admin.register(TenantSubscription)
class TenantSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("tenant", "plan", "status", "period_start", "period_end")
    list_filter = ("status",)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "is_active", "times_used")
