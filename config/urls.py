from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def service_worker(request):
    # Service workers só conseguem controlar o escopo igual ou mais raso do
    # que o caminho de onde são servidos -- por isso fica na raiz do site
    # (/sw.js) em vez de /static/js/sw.js, apesar do arquivo morar em static/.
    sw_path = settings.BASE_DIR / "static" / "src" / "js" / "sw.js"
    return HttpResponse(sw_path.read_text(encoding="utf-8"), content_type="application/javascript")


urlpatterns = [
    path("sw.js", service_worker, name="service_worker"),
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
    path("api/", include("apps.api.urls")),
    path("", include("apps.onboarding.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
