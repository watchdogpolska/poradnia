from django import template

from poradnia import get_version

register = template.Library()


@register.simple_tag
def poradnia_version():
    return get_version()
