from crispy_forms.layout import HTML, Fieldset, Layout
from dal import autocomplete, forward
from django.db.models import Q
from django.forms import ModelForm
from django.utils.html import format_html
from django.utils.timezone import now
from django.utils.translation import gettext as _

from poradnia.cases.models import Case
from poradnia.utils.action_views import AuthorMixin
from poradnia.utils.crispy_forms_helpers import (
    FormHorizontalMixin,
    SingleButtonMixin,
)
from poradnia.utils.view_mixins import UserKwargModelFormMixin

from .models import Advice, Scope

# Sent along with the selected scope so the issue/area autocomplete views
# know to filter by it (the advice list filter uses the same endpoints
# unfiltered).
SCOPE_FORWARD = ["scope", forward.Const(True, "scope_filtered")]


class AdviceForm(
    UserKwargModelFormMixin,
    FormHorizontalMixin,
    SingleButtonMixin,
    AuthorMixin,
    ModelForm,
):
    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        super().__init__(*args, **kwargs)
        self.helper.form_method = "post"
        self.fields["grant_on"].initial = now()
        case_initial = initial.get("case") or getattr(self.instance, "case", None)
        if case_initial:
            self.fields["case"].disabled = True
        else:
            self.fields["case"].queryset = Case.objects.for_user(self.user).all()
            self.fields["case"].help_text = _(
                "Select from poradnia.cases which do " "you have a permission"
            )
        self.fields["scope"].required = True
        # Keep an already assigned, since deactivated, scope selectable.
        self.fields["scope"].queryset = Scope.objects.filter(
            Q(active=True) | Q(pk=self.instance.scope_id)
        )
        self.fields["scope"].help_text = _(
            "Issues and areas to choose from depend on the selected scope. "
            "Changing the scope clears the selected issues and areas."
        )
        self.helper.layout = Layout(
            Fieldset(
                _("Statistic data"),
                "case",
                "scope",
                HTML(
                    format_html(
                        '<div id="advice-scope-status" class="visually-hidden" '
                        'role="status" data-cleared-message="{}"></div>',
                        _(
                            "The scope has changed, so the selected issues "
                            "and areas have been cleared."
                        ),
                    )
                ),
                "issues",
                "area",
                "person_kind",
                "institution_kind",
                "jst",
                "helped",
                "interesting_case",
                "for_knowledge_base",
            ),
            Fieldset(
                _("Details"),
                "subject",
                "summary",
                "grant_on",
                "advicer",
                "comment",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get("scope")
        if scope is None:
            # "scope" already carries its own required/invalid error.
            return cleaned_data
        for name in ("issues", "area"):
            self._check_scope_choices(name, scope, cleaned_data.get(name) or [])
        return cleaned_data

    def _check_scope_choices(self, name, scope, selected):
        mismatched = [obj for obj in selected if not scope.matches(obj)]
        if mismatched:
            self.add_error(
                name,
                _("Not available for the selected scope: %(names)s")
                % {"names": ", ".join(str(obj) for obj in mismatched)},
            )
        # Inactive entries already on the advice may stay; only adding new
        # ones is refused.
        already_set = (
            set(getattr(self.instance, name).values_list("pk", flat=True))
            if self.instance.pk
            else set()
        )
        inactive = [
            obj for obj in selected if not obj.active and obj.pk not in already_set
        ]
        if inactive:
            self.add_error(
                name,
                _("Inactive, cannot be added: %(names)s")
                % {"names": ", ".join(str(obj) for obj in inactive)},
            )

    class Meta:
        model = Advice
        fields = [
            "case",
            "subject",
            "summary",
            "grant_on",
            "scope",
            "issues",
            "area",
            "person_kind",
            "institution_kind",
            "advicer",
            "comment",
            "helped",
            "interesting_case",
            "for_knowledge_base",
            "jst",
        ]
        widgets = {
            "jst": autocomplete.ModelAlight(url="teryt:community-autocomplete"),
            "issues": autocomplete.ModelAlightMultiple(
                url="advicer:issue-autocomplete", forward=SCOPE_FORWARD
            ),
            "area": autocomplete.ModelAlightMultiple(
                url="advicer:area-autocomplete", forward=SCOPE_FORWARD
            ),
        }

    class Media:
        js = ["advicer/advice_form.js"]
