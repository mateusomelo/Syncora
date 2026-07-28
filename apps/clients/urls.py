from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.ClientListView.as_view(), name="list"),
    path("novo/", views.ClientCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ClientDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.ClientUpdateView.as_view(), name="update"),
    path("<int:pk>/remover/", views.ClientDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/documentos/",
        views.ClientDocumentCreateView.as_view(),
        name="document_create",
    ),
]
