from datetime import date

from django import template
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.defaultfilters import stringfilter
from django.urls import reverse

from poradnia.cases.models import Case

register = template.Library()


@register.filter
@stringfilter
def status2css(status):
    """Converts a status into css style"""
    return Case.STATUS_STYLE[status]


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


@register.filter
def letter_count_for_user(case, user):
    """Count letters for user"""
    return case.letter_set.for_user(user).count()


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


@register.simple_tag()
def current_month_url():
    today = date.today()
    return reverse("events:calendar", args=[today.strftime("%Y"), today.strftime("%m")])


@register.simple_tag()
def old_cases_to_delete_count():
    return Case.objects.old_cases_to_delete().count()


@register.simple_tag()
def old_cases_to_delete_url():
    return reverse("cases:delete_old_cases")


@register.simple_tag()
def years_to_store_cases():
    return settings.YEARS_TO_STORE_CASES
