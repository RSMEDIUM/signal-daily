from .models import Category


def category_menu(request):
    """Add categories to the template context for header navigation."""
    return {'category_menu_items': Category.objects.all()}
