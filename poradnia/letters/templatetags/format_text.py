from django import template
from django.template.defaultfilters import stringfilter, linebreaks_filter
from django.utils.safestring import mark_safe
from django.conf import settings
import mistune

register = template.Library()

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
    return mark_safe(html)