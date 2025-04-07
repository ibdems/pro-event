from django import template

register = template.Library()


@register.filter
def startswith(text, starts):
    """
    Vérifie si une chaîne commence par un certain préfixe
    Usage: {% if request.path|startswith:'/dashboard/events' %}
    """
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter
def contains(text, substring):
    """
    Vérifie si une chaîne contient une sous-chaîne
    Usage: {% if request.path|contains:'event' %}
    """
    if isinstance(text, str):
        return substring in text
    return False


@register.filter
def get_item(dictionary, key):
    """
    Récupère une valeur d'un dictionnaire par sa clé
    Usage: {{ mydict|get_item:item.id }}
    """
    return dictionary.get(key)


@register.filter
def format_currency(value):
    """
    Formate un nombre en devise (FG)
    Usage: {{ price|format_currency }}
    """
    try:
        value = float(value)
        return "{:,.0f} FG".format(value).replace(",", " ")
    except (ValueError, TypeError):
        return value
