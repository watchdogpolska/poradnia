import django_filters
from atom.ext.django_filters.filters import CrispyFilterMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, Layout, Submit
from dal import autocomplete
from django.utils.translation import gettext_lazy as _

from poradnia.teryt.filters import AreaMultipleFilter
from poradnia.users.filters import UserChoiceFilter

from .models import Advice, Area, Issue


class AdviceAreaFilter(django_filters.ModelMultipleChoiceFilter):
    """
    Filter by specifying a subset of existing `Area`s.
    """

    def __init__(self, queryset=None, widget=None, *args, **kwargs):
        queryset = queryset or Area.objects.all()
        widget = widget or autocomplete.ModelSelect2Multiple(
            url="advicer:area-autocomplete"
        )
        super().__init__(queryset=queryset, widget=widget, *args, **kwargs)


class AdviceIssueFilter(django_filters.ModelMultipleChoiceFilter):
    """
    Filter by specifying a subset of existing `Issue`s.
    """

    def __init__(self, queryset=None, widget=None, *args, **kwargs):
        queryset = queryset or Issue.objects.all()
        widget = widget or autocomplete.ModelSelect2Multiple(
            url="advicer:issue-autocomplete"
        )
        super().__init__(queryset=queryset, widget=widget, *args, **kwargs)


class AdviceFilter(CrispyFilterMixin, django_filters.FilterSet):
    subject = django_filters.CharFilter(label=_("Subject"), lookup_expr="icontains")
    advicer = UserChoiceFilter(label=_("Advicer"))
    created_by = UserChoiceFilter(label=_("Created by"))
    created_on = django_filters.DateRangeFilter(label=_("Created on"))
    community = AreaMultipleFilter(
        label=_("Community"),
        widget=autocomplete.ModelSelect2Multiple(url="teryt:community-autocomplete"),
    )
    issues = AdviceIssueFilter()
    area = AdviceAreaFilter()
    comment = django_filters.CharFilter(label=_("Comment"), lookup_expr="icontains")

    class Meta:
        model = Advice
        fields = [
            "advicer",
            "created_by",
            "created_on",
            "area",
            "issues",
            "person_kind",
            "institution_kind",
            "helped",
            "subject",
        ]
        order_by = (
            ("created_on", _("Creation date")),
            ("modified_on", _("Modification date")),
            ("id", _("ID")),
            ("advicer", _("Advicer")),
            ("person_kind", _("Person kind")),
            ("institution_kind", _("Institution kind")),
        )

    @property
    def form(self):
        self._form = super(CrispyFilterMixin, self).form
        self._form.helper = FormHelper(self._form)
        self._form.helper.form_method = "get"
        self._form.helper.form_class = "form-inline"
        self._form.helper.include_media = True
        self._form.helper.layout = Layout(
            Fieldset(
                _("Statistic data"),
                Div(
                    Div("area", css_class="col-sm-12 col-md-4"),
                    Div("issues", css_class="col-sm-12 col-md-4"),
                    Div("person_kind", css_class="col-sm-12 col-md-4"),
                    css_class="row",
                ),
                Div(
                    Div("institution_kind", css_class="col-sm-12 col-md-3"),
                    Div("helped", css_class="col-sm-12 col-md-2"),
                    Div("community", css_class="col-sm-12 col-md-7"),
                    css_class="row",
                ),
            ),
            Fieldset(
                _("Details"),
                "advicer",
                "created_by",
                "created_on",
                "subject",
                "comment",
            ),
        )
        self._form.helper.add_input(Submit("filter", _("Apply Filter")))
        return self._form
