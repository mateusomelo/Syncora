"""Estrutura da navegação principal do shell (templates/layouts/app_shell.html).

Fica em Python (não hardcoded no template) por dois motivos: precisa
resolver URLs de verdade via reverse() -- alguns itens exigem argumento
(ex.: o profissional vinculado ao usuário logado) -- e precisa decidir o
item "ativo" comparando com request.resolver_match, o que é mais claro
aqui do que dentro de tags de template.

O grupo "Módulos" não mora aqui -- é 100% dinâmico, montado a partir de
apps.verticals.registry.get_active_verticals_detail() dentro de build_nav().
"""

from django.urls import NoReverseMatch, reverse

STATIC_SECTIONS = [
    {
        "label": "Principal",
        "items": [
            {"label": "Dashboard", "icon": "home", "url_name": "dashboard:home", "namespace": "dashboard"},
            {"label": "Agenda", "icon": "calendar-days", "url_name": "scheduling:calendar_day", "namespace": "scheduling"},
            {"label": "Calendário", "icon": "calendar-sync", "url_name": "calendar_sync:professional_calendar", "requires_professional": True},
        ],
    },
    {
        "label": "Cadastros",
        "items": [
            {"label": "Clientes", "icon": "users", "url_name": "clients:list", "namespace": "clients"},
            {"label": "Funcionários", "icon": "identification", "url_name": "staff:list", "namespace": "staff"},
            {"label": "Serviços", "icon": "tag", "url_name": "services:list", "namespace": "services"},
        ],
    },
    {
        "label": "Financeiro",
        "items": [
            {"label": "Caixa", "icon": "banknotes", "url_name": "finance:cash_flow"},
            {"label": "Recebimentos", "icon": "trending-up", "url_name": "finance:revenue_list"},
            {"label": "Despesas", "icon": "receipt", "url_name": "finance:expense_list"},
            {"label": "Relatórios", "icon": "chart-bar", "url_name": "reports:home", "namespace": "reports"},
        ],
    },
    {
        "label": "Configurações",
        "items": [
            {"label": "Empresa", "icon": "building", "stub": True},
            {"label": "Usuários", "icon": "user-circle", "stub": True},
            {"label": "Permissões", "icon": "shield-check", "stub": True},
            {"label": "Integrações", "icon": "puzzle", "url_name": "calendar_sync:professional_calendar", "requires_professional": True},
            {"label": "Aparência", "icon": "swatch", "stub": True},
        ],
    },
    {
        "label": "Ajuda",
        "items": [
            {"label": "Suporte", "icon": "lifebuoy", "href": "mailto:suporte@syncora.app"},
            {"label": "Documentação", "icon": "book-open", "stub": True},
        ],
    },
]


def _resolve_item(item, view_name, namespace, professional):
    resolved = dict(item)
    resolved["active"] = False
    resolved["disabled"] = False
    resolved["href"] = item.get("href")

    if item.get("stub"):
        resolved["disabled"] = True
        return resolved

    if item.get("requires_professional"):
        if professional is None:
            resolved["disabled"] = True
            return resolved
        resolved["href"] = reverse(item["url_name"], args=[professional.pk])
        resolved["active"] = view_name == item["url_name"]
        return resolved

    if item.get("url_name"):
        try:
            resolved["href"] = reverse(item["url_name"])
        except NoReverseMatch:
            resolved["disabled"] = True
            return resolved
        resolved["active"] = view_name == item["url_name"] or (
            bool(item.get("namespace")) and namespace == item["namespace"]
        )

    return resolved


def build_nav(request, tenant, professional, active_verticals_detail):
    match = getattr(request, "resolver_match", None)
    view_name = match.view_name if match else None
    namespace = match.namespace if match else None

    sections = []
    for section in STATIC_SECTIONS:
        items = [_resolve_item(item, view_name, namespace, professional) for item in section["items"]]
        sections.append({"label": section["label"], "items": items})
        if section["label"] == "Financeiro" and active_verticals_detail:
            module_items = []
            for vertical in active_verticals_detail:
                for item in vertical["menu_items"]:
                    module_items.append(
                        {
                            "label": item["label"],
                            "icon": item.get("icon", "tag"),
                            "href": reverse(item["url_name"]),
                            "active": view_name == item["url_name"],
                            "disabled": False,
                            "group": vertical["label"],
                        }
                    )
            sections.append({"label": "Módulos", "items": module_items})

    active_section = next(
        (s["label"] for s in sections if any(i["active"] for i in s["items"])), None
    )
    return sections, active_section
