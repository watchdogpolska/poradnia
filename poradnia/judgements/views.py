from atom.ext.crispy_forms.forms import SingleButtonMixin
from atom.ext.guardian.views import RaisePermissionRequiredMixin
from atom.views import DeleteMessageMixin
from braces.forms import UserKwargModelFormMixin
from braces.views import FormValidMessageMixin, UserFormKwargsMixin
from django import forms
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, UpdateView

from poradnia.cases.models import Case
from poradnia.judgements.models import CourtCase


class CourtCaseForm(UserKwargModelFormMixin, SingleButtonMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.case = kwargs.pop("case", None)
        super().__init__(*args, **kwargs)
        if self.case:
            self.helper.form_action = reverse(
                "judgements:create", kwargs={"case_pk": self.case.pk}
            )
        else:
            self.helper.form_action = reverse(
                "judgements:update", kwargs={"pk": self.instance.pk}
            )

    def save(self, commit=True):
        if self.case:
            self.instance.case = self.case
        if self.instance.pk:
            self.instance.modified_by = self.user
        else:
            self.instance.created_by = self.user
        super().save(commit)

    class Meta:
        model = CourtCase
        fields = ["court", "signature"]


class CourtCaseCreateView(
    RaisePermissionRequiredMixin, UserFormKwargsMixin, CreateView
):
    model = CourtCase
    form_class = CourtCaseForm
    permission_required = ["cases.can_add_record"]

    @cached_property
    def case(self):
        return get_object_or_404(Case, pk=self.kwargs["case_pk"])

    def get_permission_object(self):
        return self.case

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["case"] = self.case
        return kw

    def get_context_data(self, **kwargs):
        kwargs["case"] = self.case
        return super().get_context_data(**kwargs)

    def get_form_valid_message(self):
        return _("{0} created!").format(self.object)

    def get_success_url(self):
        return self.case.get_absolute_url()


class CourtCaseUpdateView(
    RaisePermissionRequiredMixin, UserFormKwargsMixin, FormValidMessageMixin, UpdateView
):
    model = CourtCase
    form_class = CourtCaseForm
    permission_required = ["cases.can_add_record"]

    def get_permission_object(self):
        return self.get_object().case

    def get_form_valid_message(self):
        return _("{0} updated!").format(self.object)


class CourtCaseDeleteView(RaisePermissionRequiredMixin, DeleteMessageMixin, DeleteView):
    model = CourtCase
    success_url = reverse_lazy("judgements:list")
    permission_required = ["cases.can_add_record"]

    def get_permission_object(self):
        return self.get_object().case

    def get_success_message(self):
        return _("{0} deleted!").format(self.object)
