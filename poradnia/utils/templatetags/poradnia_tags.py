import re
from datetime import datetime

from django import template
from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from guardian.shortcuts import get_user_perms

from poradnia import get_version

register = template.Library()


@register.filter
def strip_wrapping_p(value):
    """
    Strips the single <p> wrapper TinyMCE 7 always emits around its
    content - even one typed line - now that forced_root_block's
    validator rejects false/"" (confirmed against the bundled
    tinymce.min.js: it requires a non-empty string and silently falls
    back to its "p" default otherwise, so disabling the wrapper via
    config is no longer possible). Needed wherever a tinycontent block
    must render inline mid-sentence rather than as its own paragraph -
    see pages/accessibility_statement.html's contact/RPO-link fields.
    Removes only the first opening <p...> (anchored at the start) and
    the first </p> that follows, so a trailing admin-only "(Edit)" link
    or genuinely multi-paragraph content passes through untouched.
    """
    value = value or ""
    value = re.sub(r"^\s*<p[^>]*>", "", value, count=1, flags=re.S)
    value = re.sub(r"</p>", "", value, count=1, flags=re.S)
    return mark_safe(value.strip())


@register.filter
def elided_page_range(page_obj):
    """
    elided_page_range filter wraps Paginator.get_elided_page_range so it can
    be used from a template {% for %} tag, which cannot pass arguments to
    a method call directly.
    """
    return page_obj.paginator.get_elided_page_range(page_obj.number)


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
    # class added so WCAG mode can target this one h1 without touching any
    # other <h1> on the page - the inline style (needed so !important can
    # still win over it in WCAG mode, see wcag.scss) carries the normal-mode
    # color unchanged.
    return mark_safe(
        f'<h1 class="app-mode-banner" style="color: red;">{settings.APP_MODE}</h1>'
    )


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

    now = datetime.now()
    if (1 <= now.month <= 4) or (now.month == 5 and now.day in [1, 2]):
        return True
    return False


@register.simple_tag(takes_context=True)
def show_alternative_donate_popup(context):
    """
    show_alternative_donate_popup tag used to display alternative donate popup
    for authenticated and unauthenticated users (but not staff) when the main
    popup is not shown
    """

    # Get the current user from context
    request = context.get("request")
    if not request or not hasattr(request, "user"):
        return False

    user = request.user

    # Don't show to staff/team members (only if they are authenticated and staff)
    if user.is_authenticated and user.is_staff:
        return False

    # Only show when main popup is not shown (outside Jan 1 - May 2)
    now = datetime.now()
    main_popup_period = (1 <= now.month <= 4) or (now.month == 5 and now.day in [1, 2])

    # Show alternative popup when main popup is not shown
    # This will show for both authenticated non-staff users and unauthenticated users
    return not main_popup_period
