from django import template
from django.template.defaultfilters import stringfilter
from cases.models import Case
register = template.Library()


@register.filter
@stringfilter
def status2css(status):
    """Converts a status into css style"""
    return {'free': 'fa fa-circle-o ',
        'open': 'fa fa-dot-circle-o',
        'closed': 'fa fa-circle'}[status]


@register.filter
@stringfilter
def status2display(status):
    """Converts a status into display name"""
    return Case.STATUS[status]
