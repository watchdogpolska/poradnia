from django import template
from django.contrib.sites.shortcuts import get_current_site
from django.template.defaultfilters import stringfilter

from poradnia.cases.models import Case

register = template.Library()

STATUS_STYLE = {
    "0": "fa fa-circle-o ",
    "1": "fa fa-dot-circle-o",
    "3": "fa fa-plus-square-o",
    "2": "fa fa-circle",
}


@register.filter
@stringfilter
def status2css(status):
    """Converts a status into css style"""
    return STATUS_STYLE[status]


@register.filter
@stringfilter
def status2display(status):
    """Converts a status into display name"""
    return Case.STATUS[status]


@register.filter
@stringfilter
def status_name(status):
    """Converts a status into name"""
    choice_names_dict = {v: k for k, v in Case.STATUS._identifier_map.items()}
    return choice_names_dict[status]


@register.simple_tag(takes_context=True)
def full_link(context, path):
    scheme = (
        "{}://".format(context["request"].scheme)
        if "request" in context
        else "https://"
    )
    return "".join(
        [
            scheme,
            get_current_site(context.get("request", None)).domain,
            path if path.startswith("/") else "/" + path,
        ]
    )
