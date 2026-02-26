from django import template

register = template.Library()


@register.filter
def fcfa(value):
    """Formatage 2 900 FCFA avec separateur espace."""
    try:
        amount = int(float(value))
    except (TypeError, ValueError):
        return "0 FCFA"
    return f"{amount:,}".replace(",", " ") + " FCFA"

