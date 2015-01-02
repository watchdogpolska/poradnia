from django.views.generic import DetailView, UpdateView, DeleteView, ListView
from django.http import Http404
from braces.views import FormValidMessageMixin
from .models import Case, Permission
from .mixins import PermissionGroupMixin


class CaseDetail(PermissionGroupMixin, DetailView):
    model = Case


class CaseList(PermissionGroupMixin, ListView):
    model = Case


class CaseEdit(FormValidMessageMixin, UpdateView, PermissionGroupMixin):
    model = Case
    fields = ("name", "status")

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
    fields = ('rank', 'user')

    def get_success_url(self):
        return self.object.case.get_absolute_url()

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)
