from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_update(context, **kwargs):
    updated = context["request"].GET.copy()
    for k, v in kwargs.items():
        updated[k] = v
    return updated.urlencode()


@register.simple_tag(takes_context=True)
def query_append(context, k=None, v=None, **kwargs):
    if k and v:
        kwargs[k] = v
    updated = context["request"].GET.copy()
    for k, v in kwargs.items():
        updated.appendlist(k, v)
    return updated.urlencode()
