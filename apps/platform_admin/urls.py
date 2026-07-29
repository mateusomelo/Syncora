from django.urls import path

from . import views

app_name = "platform_admin"

urlpatterns = [
    path("", views.TenantListView.as_view(), name="tenant_list"),
    path("tenants/novo/", views.TenantCreateView.as_view(), name="tenant_create"),
    path("tenants/<uuid:pk>/", views.TenantDetailView.as_view(), name="tenant_detail"),
    path("tenants/<uuid:pk>/editar/", views.TenantUpdateView.as_view(), name="tenant_update"),
    path("tenants/<uuid:pk>/suspender/", views.TenantSuspendView.as_view(), name="tenant_suspend"),
    path("tenants/<uuid:pk>/ativar/", views.TenantActivateView.as_view(), name="tenant_activate"),
    path("tenants/<uuid:pk>/excluir/", views.TenantDeleteView.as_view(), name="tenant_delete"),
    path(
        "tenants/<uuid:pk>/flags/<str:key>/toggle/",
        views.FeatureFlagToggleView.as_view(),
        name="feature_flag_toggle",
    ),
    path(
        "tenants/<uuid:pk>/impersonar/",
        views.ImpersonationStartView.as_view(),
        name="impersonation_start",
    ),
    path("impersonacao/sair/", views.ImpersonationStopView.as_view(), name="impersonation_stop"),
    path("impersonacao/", views.ImpersonationActiveView.as_view(), name="impersonation_active"),
]
