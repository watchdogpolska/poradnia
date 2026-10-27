from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext
from django.views.decorators.http import require_POST

from .messages_catalog import CATALOG
from .ui_mode import UI_MODE_COOKIE_NAME, UI_MODES


def _render_example(entry):
    try:
        if entry.build is not None:
            return entry.build()
        text = gettext(entry.msgid) if entry.translated else entry.msgid
        return entry.render(text)
    except (
        Exception
    ) as exc:  # noqa: BLE001 - surface render errors in the preview itself
        return "BŁĄD RENDEROWANIA: {}: {}".format(type(exc).__name__, exc)


@staff_member_required
def messages_catalog_view(request):
    groups = {}
    for entry in CATALOG:
        groups.setdefault(entry.group, []).append(
            {"entry": entry, "text": _render_example(entry)}
        )

    context = admin.site.each_context(request)
    context.update(
        {
            "groups": groups,
            "title": "Katalog komunikatów wyświetlanych przez aplikację",
        }
    )
    return render(request, "utils/messages_catalog.html", context)


@require_POST
def ui_mode_view(request):
    mode = request.POST.get("mode")
    if mode not in UI_MODES:
        return HttpResponseBadRequest("Invalid ui_mode value")

    next_url = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = "/"

    response = redirect(next_url)
    response.set_cookie(
        UI_MODE_COOKIE_NAME,
        mode,
        max_age=60 * 60 * 24 * 365,
        samesite="Lax",
    )
    return response
