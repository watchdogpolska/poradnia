import six
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter()
def join_attr(values, attr):
    values = [getattr(o, attr) for o in values]
    values = [str(o) if isinstance(o, six.integer_types) else '"{}"'.format(conditional_escape(o))
              for o in values]
    return mark_safe(", ".join(values))
