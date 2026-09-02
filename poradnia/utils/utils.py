from django.utils.text import slugify


def slugify_unicode(value):
    """AUTOSLUG_SLUGIFY_FUNCTION target; replaces unmaintained unicode-slugify."""
    return slugify(value, allow_unicode=True)


def get_numeric_param(request, key):
    """Get numeric param from request"""
    value = None
    try:
        value = int(request.POST.get(key))
    except (TypeError, ValueError):
        pass
    return value
