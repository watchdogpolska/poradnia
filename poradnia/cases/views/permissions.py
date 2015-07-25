from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from braces.views import UserFormKwargsMixin, FormValidMessageMixin
from users.forms import TranslatedManageObjectPermissionForm, TranslatedUserObjectPermissionsForm
from ..models import Case
from ..forms import CaseGroupPermissionForm


def assign_perm_check(user, case):
    if case.status == case.STATUS.free:
        if not (user.has_perm('cases.can_assign')):
            raise PermissionDenied
    else:
        case.perm_check(user, 'can_manage_permission')
    return True


class UserPermissionCreateView(UserFormKwargsMixin, FormView):
    form_class = TranslatedManageObjectPermissionForm
    template_name = 'cases/case_form_permission_add.html'

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(UserPermissionCreateView, self).get_form_kwargs(*args, **kwargs)
        self.case = get_object_or_404(Case, pk=self.kwargs['pk'])
        assign_perm_check(self.request.user, self.case)
        kwargs.update({'obj': self.case})
        return kwargs

    def form_valid(self, form):
        form.save_obj_perms()
        for user in form.cleaned_data['users']:
            self.case.send_notification(actor=self.request.user, staff=True, verb='granted')
            messages.success(self.request,
                _("Success granted permission of %(user)s to %(case)s") %
                {'user': user, 'case': self.case})
        self.case.status_update()
        return super(UserPermissionCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('cases:detail', kwargs={'pk': str(self.case.pk)})

    def get_context_data(self, **kwargs):
        context = super(UserPermissionCreateView, self).get_context_data(**kwargs)
        context['object'] = self.case
        return context


class UserPermissionUpdateView(FormValidMessageMixin, FormView):
    form_class = TranslatedUserObjectPermissionsForm
    template_name = 'cases/case_form_permission_update.html'

    def get_form_kwargs(self):
        kwargs = super(UserPermissionUpdateView, self).get_form_kwargs()
        self.case = get_object_or_404(Case, pk=self.kwargs['pk'])
        assign_perm_check(self.request.user, self.case)
        self.action_user = get_object_or_404(get_user_model(), username=self.kwargs['username'])
        kwargs.update({'user': self.action_user, 'obj': self.case})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UserPermissionUpdateView, self).get_context_data(**kwargs)
        context['object'] = self.case
        return context

    def get_form_valid_message(self):
        return _("Updated permission %(user)s to %(case)s!") %\
            ({'user': self.action_user, 'case': self.case})

    def get_success_url(self):
        return reverse('cases:detail', kwargs={'pk': str(self.case.pk)})


class CaseGroupPermissionView(FormValidMessageMixin, SingleObjectMixin, FormView):
    model = Case
    form_class = CaseGroupPermissionForm
    template_name = 'cases/case_form.html'

    def get_form_valid_message(self):
        return _("%(user)s granted permissions from %(group)s!") % (self.form.cleaned_data)

    def get_form_kwargs(self):
        kwargs = super(CaseGroupPermissionView, self).get_form_kwargs()
        self.object = self.get_object()
        kwargs.update({'case': self.object, 'user': self.request.user})
        return kwargs

    def form_valid(self, form, *args, **kwargs):
        self.form = form
        form.assign()
        return super(CaseGroupPermissionView, self).form_valid(form=form, *args, **kwargs)

    def get_success_url(self):
        return reverse('cases:detail', kwargs={'pk': str(self.object.pk)})

    def get_object(self):
        obj = super(CaseGroupPermissionView, self).get_object()
        assign_perm_check(self.request.user, obj)
        return obj
