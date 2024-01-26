from django import template
from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from guardian.shortcuts import get_user_perms

from poradnia import get_version

register = template.Library()


@register.simple_tag
def poradnia_version():
    return get_version()


@register.simple_tag
def app_mode():
    """
    app_mode tag used to differentiate dev, demo and production environments
    use "DEV", "DEMO" and "PROD" values in env variable APP_MODE
    """
    if settings.APP_MODE == "PROD":
        return mark_safe("")
    return mark_safe(f'<h1 style="color: red;">{settings.APP_MODE}</h1>')


@register.simple_tag
def app_main_style():
    """
    app_main_style tag used to differentiate dev, demo and production environments
    use "DEV", "DEMO" and "PROD" values in env variable APP_MODE
    """
    if settings.APP_MODE == "PROD":
        return mark_safe('<div class="main">')
    elif settings.APP_MODE == "DEV":
        return mark_safe('<div class="main" style="background-color: #d3e20040;">)')
    return mark_safe('<div class="main" style="background-color: #60e20040;">)')


@register.simple_tag
def user_obj_perms_list(user, obj):
    """
    user_obj_perms_list tag used to display object permissions
    """
    perms = get_user_perms(user, obj)
    perm_list = [Permission.objects.get(codename=perm) for perm in perms]
    perm_name_list = [gettext(perm.name) for perm in perm_list]
    return ", ".join(sorted(perm_name_list))


@register.simple_tag
def show_donate_popup():
    """
    show_donate_popup tag used to display donate popup between Jan 1 and May 2nd
    inclusive, every year
    """
    from datetime import datetime

    now = datetime.now()
    if (1 <= now.month <= 4) or (now.month == 5 and now.day in [1, 2]):
        return True
    return False
