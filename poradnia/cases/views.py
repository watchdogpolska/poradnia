from django.views.generic import DetailView, UpdateView, CreateView, DeleteView, ListView
from django.http import Http404
from braces.views import FormValidMessageMixin
from .models import Case, Permission
from .mixins import PermissionGroupMixin


class CaseDetail(PermissionGroupMixin, DetailView):
    model = Case


class CaseList(PermissionGroupMixin, ListView):
    model = Case

    def get_queryset(self, *args, **kwargs):
        queryset = super(CaseList, self).get_queryset(*args, **kwargs)
        return queryset.without_lawyers()


class CaseEdit(FormValidMessageMixin, UpdateView, PermissionGroupMixin):
    model = Case
    fields = ("name", "status")

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)


class PermissionCreate(FormValidMessageMixin, PermissionGroupMixin, CreateView):
    model = Permission
    fields = ('user', 'rank')

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
    fields = ('rank', 'user')

    def get_success_url(self):
        return self.object.case.get_absolute_url()

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)
