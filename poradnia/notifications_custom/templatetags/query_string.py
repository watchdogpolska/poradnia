from django import template
register = template.Library()


@register.simple_tag
def query_update(request, **kwargs):
    # import ipdb; ipdb.set_trace()
    updated = request.GET.copy()
    updated.update(kwargs)
    return updated.urlencode()


@register.simple_tag
def query_extend(request, k=None, v=None, **kwargs):
    if k and v:
        kwargs[k] = v
    updated = request.GET.copy()
    for k, v in kwargs.items():
        updated.appendlist(k, v)
    return updated.urlencode()


@register.simple_tag
def test(test):
    import ipdb
    ipdb.set_trace()
