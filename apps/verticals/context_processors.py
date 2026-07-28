from .registry import get_active_menu_items, get_active_verticals, get_active_verticals_detail


def verticals(request):
    tenant = getattr(request, "tenant", None)
    return {
        "active_verticals": get_active_verticals(tenant),
        "vertical_menu_items": get_active_menu_items(tenant),
        "active_verticals_detail": get_active_verticals_detail(tenant),
    }
