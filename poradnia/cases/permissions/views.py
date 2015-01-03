from django.contrib.auth import get_user_model
from django.views.generic import CreateView, UpdateView, DeleteView
from braces.views import FormValidMessageMixin
from ..mixins import PermissionGroupMixin
from .models import Permission, LocalGroup


class PermissionCreate(FormValidMessageMixin, PermissionGroupMixin, CreateView):
    model = Permission
    fields = ('user', 'group')

    def get_form(self, *args, **kwargs):  # TODO: Correct excluding
        User = get_user_model()
        form = super(PermissionCreate, self).get_form(*args, **kwargs)
        form.fields['group'].limit_choices_to = [sg.group_id for sg in LocalGroup.all()]
        form.fields['user'].limit_choices_to = [u.pk for u in User.objects.exclude(permission__case_id=self.kwargs['case_id']).all()]  # Exclude exists user
        return form

    def form_valid(self, form):
        form.instance.case_id = self.kwargs['case_id']
        return super(PermissionCreate, self).form_valid(form)

    def get_success_url(self):
        return self.object.case.get_absolute_url()

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)


class PermissionDelete(FormValidMessageMixin, PermissionGroupMixin, DeleteView):
    model = Permission

    def get_success_url(self):
        return self.object.case.get_absolute_url()

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)


class PermissionUpdate(FormValidMessageMixin, PermissionGroupMixin, UpdateView):
    model = Permission
    fields = ('group', 'user')

    def get_success_url(self):
        return self.object.case.get_absolute_url()

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)
