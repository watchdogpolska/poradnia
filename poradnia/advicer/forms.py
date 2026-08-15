from atom.forms import AuthorMixin
from braces.forms import UserKwargModelFormMixin
from crispy_forms.layout import Fieldset, Layout
from dal import autocomplete
from django.forms import ModelForm
from django.utils.timezone import now
from django.utils.translation import gettext as _

from poradnia.cases.models import Case
from poradnia.utils.crispy_forms import (
    FormHorizontalMixin,
    SingleButtonMixin,
)

from .models import Advice


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
        self.helper.layout = Layout(
            Fieldset(
                _("Statistic data"),
                "case",
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

    class Meta:
        model = Advice
        fields = [
            "case",
            "subject",
            "summary",
            "grant_on",
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
                url="advicer:issue-autocomplete"
            ),
            "area": autocomplete.ModelAlightMultiple(url="advicer:area-autocomplete"),
        }
