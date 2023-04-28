import mistune
from bleach.sanitizer import Cleaner
from django import template
from django.conf import settings
from django.template.defaultfilters import linebreaks_filter, stringfilter
from django.utils.safestring import mark_safe

register = template.Library()
cleaner = Cleaner(
    tags=settings.BLEACH_ALLOWED_TAGS,
    attributes=settings.BLEACH_ALLOWED_ATTRIBUTES,
)


@register.filter()
@stringfilter
def format_text(text):
    if settings.RICH_TEXT_ENABLED:
        return parse_markdown(text)
    else:
        return linebreaks_filter(text)


def parse_markdown(text):
    md = mistune.create_markdown()
    html = md(text)
    sanitized = cleaner.clean(html)
    return mark_safe(sanitized)
