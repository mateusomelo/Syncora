from django.urls import path

from . import views

app_name = "barber"

urlpatterns = [
    path("pacotes/", views.PackageListView.as_view(), name="package_list"),
    path("pacotes/novo/", views.PackageCreateView.as_view(), name="package_create"),
    path("pacotes/<int:pk>/editar/", views.PackageUpdateView.as_view(), name="package_update"),
    path("produtos/", views.ProductListView.as_view(), name="product_list"),
    path("produtos/novo/", views.ProductCreateView.as_view(), name="product_create"),
    path("produtos/<int:pk>/editar/", views.ProductUpdateView.as_view(), name="product_update"),
    path("pacotes-clientes/", views.ClientPackageListView.as_view(), name="client_package_list"),
    path(
        "pacotes-clientes/novo/",
        views.ClientPackageCreateView.as_view(),
        name="client_package_create",
    ),
    path(
        "pacotes-clientes/<int:pk>/usar/",
        views.ClientPackageUseSessionView.as_view(),
        name="client_package_use",
    ),
    path("caixa/", views.CashRegisterView.as_view(), name="cash_register"),
    path("caixa/abrir/", views.CashRegisterOpenView.as_view(), name="cash_register_open"),
    path("caixa/<int:pk>/fechar/", views.CashRegisterCloseView.as_view(), name="cash_register_close"),
    path(
        "caixa/<int:pk>/movimento/",
        views.CashMovementCreateView.as_view(),
        name="cash_movement_create",
    ),
]
