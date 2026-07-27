from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.translation import gettext

from .messages_catalog import CATALOG


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
