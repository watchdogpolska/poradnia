from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

import markdown as md
from bleach.sanitizer import Cleaner


cleaner = Cleaner(
tags=['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'hr', 'pre', 'img'],
attributes={'a': ['href', 'title'],'img': ['alt', 'src', 'title'] ,'abbr': ['title'], 'acronym': ['title']})

register = template.Library()


@register.filter()
@stringfilter
def markdown(value):
    markdown = md.markdown(value, extensions=['markdown.extensions.fenced_code', 'sane_lists'])
    sanitized = cleaner.clean(markdown)
    return mark_safe(sanitized)