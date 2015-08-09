from django import template
from django.template.defaultfilters import stringfilter
from cases.models import Case


register = template.Library()


@register.filter
@stringfilter
def status2css(status):
    """Converts a status into css style"""
    return {u'0': 'fa fa-circle-o ',
        u'1': 'fa fa-dot-circle-o',
        u'2': 'fa fa-circle'}[status]


@register.filter
@stringfilter
def status2display(status):
    """Converts a status into display name"""
    return Case.STATUS[status]
