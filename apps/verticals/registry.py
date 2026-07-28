"""Registry dos módulos verticais (barbearia/odontologia/psicologia).

Sem lógica de negócio própria — só decide, a partir das FeatureFlag da
empresa, quais verticais estão ativos e quais itens de menu mostrar. Cada
vertical continua sendo um app Django independente em apps/verticals/*;
o core nunca importa esses apps diretamente (só via este registry, que lê
FeatureFlag, e via signals — ver apps/verticals/*/signals.py)."""

from django.http import Http404

from apps.tenants.models import FeatureFlag

VERTICALS = {
    "barbearia": {
        "label": "Barbearia",
        "icon": "scissors",
        "flag_key": FeatureFlag.Key.BARBEARIA,
        "menu_items": [
            {"label": "Pacotes", "url_name": "barber:package_list", "icon": "tag"},
            {"label": "Produtos", "url_name": "barber:product_list", "icon": "tag"},
            {"label": "Caixa", "url_name": "barber:cash_register", "icon": "banknotes"},
        ],
    },
    "odontologia": {
        "label": "Odontologia",
        "icon": "tooth",
        "flag_key": FeatureFlag.Key.ODONTOGRAMA,
        "menu_items": [
            {"label": "Pacientes", "url_name": "dentistry:patient_list", "icon": "users"},
            {"label": "Orçamentos", "url_name": "dentistry:budget_list", "icon": "receipt"},
        ],
    },
    "psicologia": {
        "label": "Psicologia",
        "icon": "chat-heart",
        "flag_key": FeatureFlag.Key.PSICOLOGIA,
        "menu_items": [
            {"label": "Prontuários", "url_name": "psychology:clinical_record_list", "icon": "clipboard"},
        ],
    },
}


def get_active_verticals(tenant):
    if tenant is None:
        return []
    enabled_keys = set(
        FeatureFlag.objects.filter(tenant=tenant, enabled=True).values_list("key", flat=True)
    )
    return [key for key, config in VERTICALS.items() if config["flag_key"] in enabled_keys]


def get_active_menu_items(tenant):
    items = []
    for key in get_active_verticals(tenant):
        items.extend(VERTICALS[key]["menu_items"])
    return items


def get_active_verticals_detail(tenant):
    """Como get_active_verticals, mas devolve a config completa de cada
    vertical (label, ícone, itens de menu) — usado pela navegação lateral
    para agrupar os itens sob o nome de cada módulo em vez de uma lista
    plana."""
    return [
        {"key": key, **VERTICALS[key]}
        for key in get_active_verticals(tenant)
    ]


class VerticalRequiredMixin:
    """Recusa acesso (404) se a empresa não tiver o módulo vertical
    habilitado via FeatureFlag. Complementa o registry (que só esconde o
    item de menu) impedindo acesso direto pela URL a um módulo desativado."""

    vertical_key = None

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        if self.vertical_key not in get_active_verticals(tenant):
            raise Http404("Este módulo não está habilitado para esta empresa.")
        return super().dispatch(request, *args, **kwargs)
