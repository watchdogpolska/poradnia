from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from .email_catalog import CATALOG


def _render(template_name, context):
    if not template_name:
        return None
    try:
        return render_to_string(template_name, context)
    except TemplateDoesNotExist:
        return "(brak szablonu: {})".format(template_name)
    except (
        Exception
    ) as exc:  # noqa: BLE001 - surface render errors in the preview itself
        return "BŁĄD RENDEROWANIA: {}: {}".format(type(exc).__name__, exc)


@staff_member_required
def email_catalog_view(request):
    groups = {}
    for entry in CATALOG:
        context = entry.context()
        txt = _render(entry.txt_template, context)
        html = _render(entry.html_template, context)

        if entry.split_subject and txt:
            subject, _, txt = txt.strip().partition("\n")
        elif entry.subject_template:
            subject = _render(entry.subject_template, context)
            subject = subject.strip() if subject else subject
        else:
            subject = None

        groups.setdefault(entry.group, []).append(
            {
                "entry": entry,
                "subject": subject,
                "txt": txt,
                "html": html,
            }
        )

    context = admin.site.each_context(request)
    context.update(
        {"groups": groups, "title": "Katalog e-maili wysyłanych przez aplikację"}
    )
    return render(request, "template_mail/email_catalog.html", context)
