from atom.ext.crispy_forms.forms import (
    FormHorizontalMixin,
    HelperMixin,
    SingleButtonMixin,
)
from braces.forms import UserKwargModelFormMixin
from crispy_forms.layout import Submit
from dal import autocomplete
from django import forms
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm

from ..letters.models import Letter
from ..records.models import Record
from .models import Case, PermissionGroup


class CaseForm(
    UserKwargModelFormMixin, FormHorizontalMixin, SingleButtonMixin, forms.ModelForm
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "instance" in kwargs:
            self.helper.form_action = kwargs["instance"].get_edit_url()

    def save(self, commit=True, *args, **kwargs):
        obj = super().save(commit=False, *args, **kwargs)
        if obj.pk:  # old
            obj.modified_by = self.user
            if obj.status == Case.STATUS.assigned:
                obj.send_notification(
                    actor=self.user,
                    user_qs=obj.get_users_with_perms().filter(is_staff=True),
                    verb="updated",
                )
        else:  # new
            obj.send_notification(
                actor=self.user,
                user_qs=obj.get_users_with_perms().filter(is_staff=True),
                verb="created",
            )
            obj.created_by = self.user
        if commit:
            obj.save()
        return obj

    class Meta:
        model = Case
        fields = ("name", "status", "has_project")


class CaseGroupPermissionForm(HelperMixin, forms.Form):
    action_text = _("Grant")
    user = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=autocomplete.ModelSelect2("users:autocomplete"),
        label=_("User"),
    )
    group = forms.ModelChoiceField(
        queryset=PermissionGroup.objects.all(), label=_("Permissions group")
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.case = kwargs.pop("case")
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = get_user_model().objects.for_user(self.user)
        self.helper.form_class = "form-inline"
        self.helper.layout.append(Submit("grant", _("Grant")))

        self.helper.form_action = reverse(
            "cases:permission_grant", kwargs={"pk": str(self.case.pk)}
        )

    def assign(self):
        perms = list(self.cleaned_data["group"].permissions.all())
        self.cleaned_data["user"].caseuserobjectpermission_set.filter(
            content_object=self.case
        ).exclude(permission__in=perms).delete()

        for perm in perms:
            assign_perm(perm, self.cleaned_data["user"], self.case)
        self.case.update_status()
        self.case.send_notification(
            actor=self.user,
            verb="grant_group",
            action_object=self.cleaned_data["user"],
            action_target=self.cleaned_data["group"],
            user_qs=self.case.get_users_with_perms().filter(is_staff=True),
        )


class CaseCloseForm(UserKwargModelFormMixin, HelperMixin, forms.ModelForm):
    # skip user notification, code left for potential future use
    # notify = forms.BooleanField(required=False, label=_("Notify user"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.add_input(Submit("action", _("Close"), css_class="btn-primary"))

        if "instance" in kwargs:
            self.helper.form_action = kwargs["instance"].get_close_url()

    def save(self, commit=True, *args, **kwargs):
        obj = super().save(commit=False, *args, **kwargs)
        # skip user notification
        # obj.close(actor=self.user, notify=self.cleaned_data["notify"])
        obj.close(actor=self.user, notify=False)
        if commit:
            obj.save()
        return obj

    class Meta:
        model = Case
        fields = ()


class CaseMergeForm(UserKwargModelFormMixin, HelperMixin, forms.ModelForm):
    target = forms.ModelChoiceField(
        label=_("Destination case"),
        queryset=Case.objects.none(),
        required=True,
        widget=autocomplete.ModelSelect2(url="cases:autocomplete"),
        help_text=_(
            "The selected case will receive all letters, "
            + "events, etc. from the current case."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.add_input(Submit("action", _("Merge"), css_class="btn-primary"))
        self.fields["target"].queryset = Case.objects.for_user(self.user).all()

        self.helper.form_action = reverse(
            "cases:merge", kwargs={"pk": kwargs["instance"].pk}
        )

    def create_letter(self, case):
        target = self.cleaned_data["target"]
        source = self.instance
        msg = Letter.objects.create(
            case=case,
            genre=Letter.GENRE.comment,
            created_by=self.user,
            created_by_is_staff=self.user.is_staff,
            text=_("Case #{source} have been merged with case #{target}").format(
                source=source.pk, target=target.pk
            ),
            status=Letter.STATUS.staff,
        )
        msg.send_notification(actor=self.user, verb="drop_a_note")

    def save(self, *args, **kwargs):
        target = self.cleaned_data["target"]
        source = self.instance
        Record.objects.filter(case=source).move(target)
        self.create_letter(target)
        self.create_letter(source)
        source.close(actor=self.user, notify=False)
        source.save()
        return source

    class Meta:
        model = Case
        fields = ()
