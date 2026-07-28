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
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
