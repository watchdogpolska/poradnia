from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    return mapping.get(key)
