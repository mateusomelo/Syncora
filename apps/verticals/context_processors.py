from .registry import get_active_menu_items, get_active_verticals


def verticals(request):
    tenant = getattr(request, "tenant", None)
    return {
        "active_verticals": get_active_verticals(tenant),
        "vertical_menu_items": get_active_menu_items(tenant),
    }
