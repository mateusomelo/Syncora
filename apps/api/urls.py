from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.clients.api import ClientViewSet
from apps.scheduling.api import AppointmentViewSet
from apps.services.api import ServiceViewSet
from apps.staff.api import ProfessionalViewSet

app_name = "api"

router = DefaultRouter()
router.register("clientes", ClientViewSet, basename="client")
router.register("profissionais", ProfessionalViewSet, basename="professional")
router.register("servicos", ServiceViewSet, basename="service")
router.register("agendamentos", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
    path("v1/", include(router.urls)),
]
