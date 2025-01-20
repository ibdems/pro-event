from django.template import Library

register = Library()


@register.filter
def default_if_none(value):
    return value if value is not None else ""
