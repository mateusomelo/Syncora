"""Registry dos módulos verticais (barbearia/odontologia/psicologia).

Sem lógica de negócio própria — só decide, a partir das FeatureFlag da
empresa, quais verticais estão ativos e quais itens de menu mostrar. Cada
vertical continua sendo um app Django independente em apps/verticals/*;
o core nunca importa esses apps diretamente (só via este registry, que lê
FeatureFlag, e via signals — ver apps/verticals/*/signals.py)."""

from django.http import Http404

from apps.tenants.models import FeatureFlag

# Tema fixo por segmento (cores só -- ver apps/branding/context_processors.py).
# A empresa não escolhe essas cores; só a logo continua editável em
# Configurações > Aparência. Quando nenhum módulo vertical está ativo, usa
# DEFAULT_THEME (a mesma identidade do site público: ink + azul #3b5bff).
DEFAULT_THEME = {
    "color_primary": "#3b5bff",
    "color_secondary": "#6b7280",
    "color_button": "#3b5bff",
    "color_link": "#3b5bff",
    "color_sidebar": "#12141a",
    "color_topbar": "#ffffff",
    "color_card": "#ffffff",
    "color_icons": "#3b5bff",
}

VERTICALS = {
    "barbearia": {
        "label": "Barbearia",
        "icon": "scissors",
        "flag_key": FeatureFlag.Key.BARBEARIA,
        "theme": {
            "color_primary": "#b45309",
            "color_secondary": "#78716c",
            "color_button": "#b45309",
            "color_link": "#b45309",
            "color_sidebar": "#1c1917",
            "color_topbar": "#ffffff",
            "color_card": "#ffffff",
            "color_icons": "#b45309",
        },
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
        "theme": {
            "color_primary": "#0284c7",
            "color_secondary": "#64748b",
            "color_button": "#0284c7",
            "color_link": "#0284c7",
            "color_sidebar": "#0c4a6e",
            "color_topbar": "#ffffff",
            "color_card": "#ffffff",
            "color_icons": "#0284c7",
        },
        "menu_items": [
            {"label": "Pacientes", "url_name": "dentistry:patient_list", "icon": "users"},
            {"label": "Orçamentos", "url_name": "dentistry:budget_list", "icon": "receipt"},
        ],
    },
    "psicologia": {
        "label": "Psicologia",
        "icon": "chat-heart",
        "flag_key": FeatureFlag.Key.PSICOLOGIA,
        "theme": {
            "color_primary": "#0d9488",
            "color_secondary": "#6b7280",
            "color_button": "#0d9488",
            "color_link": "#0d9488",
            "color_sidebar": "#134e4a",
            "color_topbar": "#ffffff",
            "color_card": "#ffffff",
            "color_icons": "#0d9488",
        },
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


def get_active_vertical_key(tenant):
    """A chave (ex.: "barbearia") do módulo que decide o tema hoje -- mesma
    prioridade de get_active_theme(), só que devolvendo a chave em vez do
    dict de cores. None quando nenhum módulo está ativo (tema padrão).
    Usado pra escolher qual ilustração mostrar (não só qual cor)."""
    active = get_active_verticals(tenant)
    for key in VERTICALS:
        if key in active:
            return key
    return None


def get_active_theme(tenant):
    """Tema de cor da empresa, decidido 100% pelo módulo vertical ativo --
    não é escolha da empresa (ver Configurações > Aparência, que só edita
    logo). Com mais de um módulo ativo ao mesmo tempo, vale a ordem de
    VERTICALS acima (barbearia > odontologia > psicologia); sem nenhum
    módulo, cai no DEFAULT_THEME (a mesma identidade do site público)."""
    active = get_active_verticals(tenant)
    for key in VERTICALS:
        if key in active:
            return VERTICALS[key]["theme"]
    return DEFAULT_THEME


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
