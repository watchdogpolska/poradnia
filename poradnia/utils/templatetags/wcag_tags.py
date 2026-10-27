from django import template

register = template.Library()


@register.inclusion_tag("wcag/_form_error_summary.html", takes_context=True)
def form_error_summary(context, form):
    """
    WCAG-mode-only error summary for a bound form: a list of every field
    error (linked to its field) plus any non-field errors, rendered above
    the form. No-ops (renders nothing) outside WCAG mode or when the form
    has no errors - see logs/wcag/plan/plan.md M1 (crispy error-rendering
    gap) and audit/findings.csv F007/F012.

    Deliberately not a crispy template-pack override: crispy_bootstrap5's
    own templates hardcode "bootstrap5/..." paths in several places (e.g.
    uni_form.html's {% include "bootstrap5/errors.html" %}), so a sibling
    "bootstrap5_wcag" pack would have to fork that whole include chain to
    inject one extra block - fragile against any future crispy_bootstrap5
    upgrade. A plain inclusion tag, called once per form template, avoids
    that fork entirely. (aria-invalid/aria-describedby, the other two
    items this gap was originally scoped to fix, turned out to already be
    added automatically by Django 5.2's own BoundField - confirmed by
    rendering a bound field with an error and inspecting the HTML output -
    so there was nothing left to fix there.)
    """
    return {"form": form, "ui_mode": context.get("ui_mode")}
