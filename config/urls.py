from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("apps.authentication.urls")),
    path("platform-admin/", include("apps.platform_admin.urls")),
    path("app/clientes/", include("apps.clients.urls")),
    path("app/profissionais/", include("apps.staff.urls")),
    path("app/servicos/", include("apps.services.urls")),
    path("app/agenda/", include("apps.scheduling.urls")),
    path("app/financeiro/", include("apps.finance.urls")),
    path("app/relatorios/", include("apps.reports.urls")),
    path("app/", include("apps.dashboard.urls")),
    path("app/", include("apps.calendar_sync.urls")),
    path("calendar-sync/", include("apps.calendar_sync.urls_callback")),
    path("app/barbearia/", include("apps.verticals.barber.urls")),
    path("app/odontologia/", include("apps.verticals.dentistry.urls")),
    path("app/psicologia/", include("apps.verticals.psychology.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
