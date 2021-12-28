from atom.ext.guardian.views import RaisePermissionRequiredMixin
from atom.views import ActionMessageMixin, ActionView
from braces.views import FormValidMessageMixin
from cached_property import cached_property
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import FormView
from guardian.shortcuts import get_perms

from poradnia.users.forms import (
    TranslatedManageObjectPermissionForm,
    TranslatedUserObjectPermissionsForm,
)
from poradnia.users.models import User

from ..forms import CaseGroupPermissionForm
from ..models import Case, CaseUserObjectPermission

from django.urls import reverse


class CasePermissionTestMixin(RaisePermissionRequiredMixin):
    accept_global_perms = True

    @cached_property
    def case(self):
        return get_object_or_404(Case, pk=self.kwargs["pk"])

    def get_permission_object(self):
        return self.case

    def get_required_permissions(self, request=None):
        if self.case.status == self.case.STATUS.free:
            return ["cases.can_assign"]
        else:
            return ["cases.can_manage_permission"]


class UserPermissionCreateView(CasePermissionTestMixin, FormView):
    form_class = TranslatedManageObjectPermissionForm
    template_name = "cases/case_form_permission_add.html"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({"obj": self.case, "actor": self.request.user})
        return kwargs

    def form_valid(self, form):
        form.save_obj_perms()
        for user in form.cleaned_data["users"]:
            self.case.send_notification(
                actor=self.request.user,
                user_qs=self.case.get_users_with_perms().filter(is_staff=True),
                verb="granted",
            )
            messages.success(
                self.request,
                _("Success granted permission of %(user)s to %(case)s").format(
                    user=user, case=self.case
                ),
            )
        self.case.status_update()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("cases:detail", kwargs={"pk": str(self.case.pk)})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.case
        return context


class UserPermissionUpdateView(
    CasePermissionTestMixin, FormValidMessageMixin, FormView
):
    form_class = TranslatedUserObjectPermissionsForm
    template_name = "cases/case_form_permission_update.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.action_user = get_object_or_404(
            get_user_model(), username=self.kwargs["username"]
        )
        kwargs.update({"user": self.action_user, "obj": self.case})
        del kwargs["initial"]
        return kwargs

    def get_obj_perms_field_initial(self, *args, **kwargs):
        return get_perms(self.action_user, self.case)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.case
        context["action_user"] = self.action_user
        return context

    def form_valid(self, form):
        form.save_obj_perms()
        self.case.status_update()
        return super().form_valid(form)

    def get_form_valid_message(self):
        return _("Updated permission %(user)s to %(case)s!").format(
            user=self.action_user, case=self.case
        )

    def get_success_url(self):
        return self.case.get_absolute_url()


class CaseGroupPermissionView(CasePermissionTestMixin, FormValidMessageMixin, FormView):
    model = Case
    form_class = CaseGroupPermissionForm
    template_name = "cases/case_form.html"

    def get_form_valid_message(self):
        return _("{user} granted permissions from {group}!").format(
            **self.form.cleaned_data
        )

    def get_form_kwargs(self):
        self.object = self.get_object()
        kwargs = super().get_form_kwargs()
        kwargs.update({"case": self.object, "user": self.request.user})
        return kwargs

    def form_valid(self, form, *args, **kwargs):
        self.form = form
        form.assign()
        self.case.status_update()
        return super().form_valid(form=form, *args, **kwargs)

    def get_success_url(self):
        return reverse("cases:detail", kwargs={"pk": str(self.object.pk)})

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["object"] = self.object
        return context

    def get_object(self):
        return self.case


class UserPermissionRemoveView(
    RaisePermissionRequiredMixin, ActionMessageMixin, ActionView
):
    model = Case
    permission_required = "cases.can_manage_permission"
    template_name_suffix = "_permission_remove_confirm"

    def get_permission_object(self):
        return None

    @cached_property
    def user(self):
        return get_object_or_404(User, username=self.kwargs["username"])

    def action(self):
        CaseUserObjectPermission.objects.filter(
            user=self.user, content_object=self.object
        ).delete()
        self.object.status_update()

    def get_success_message(self):
        return _('Removed all permission of "{user}" in case "{case}"').format(
            user=self.user, case=self.object
        )

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()
