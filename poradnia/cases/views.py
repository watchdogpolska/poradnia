from django.views.generic import DetailView, UpdateView, ListView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from braces.views import FormValidMessageMixin, PermissionRequiredMixin, LoginRequiredMixin
from .models import Case
from .permissions.mixins import PermissionGroupMixin, PermissionGroupQuerySetMixin
from .tags.models import Tag


class CaseDetail(LoginRequiredMixin, PermissionGroupMixin, DetailView):
    model = Case


class CaseList(LoginRequiredMixin, PermissionGroupQuerySetMixin, ListView):
    model = Case


class CaseObjectMixin(object):
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CaseObjectMixin, self).get_context_data(**kwargs)
        # Add in the publisher
        context['object'] = self.object
        return context


class CaseListUser(CaseObjectMixin, ListView):
    model = Case
    template_name_suffix = '_list_for_user'

    def get_queryset(self, *args, **kwargs):
        queryset = super(CaseListUser, self).get_queryset(*args, **kwargs)
        user_queryset = get_user_model().objects.for_user(self.request.user)
        self.object = get_object_or_404(user_queryset, username=self.kwargs['username'])
        return queryset.filter(client=self.object).with_last_send_letter()


class CaseListTag(CaseObjectMixin, ListView):
    model = Case
    template_name_suffix = '_list_for_tag'

    def get_queryset(self, *args, **kwargs):
        queryset = super(CaseListTag, self).get_queryset(*args, **kwargs)
        self.object = get_object_or_404(Tag, pk=self.kwargs['tag_pk'])
        return queryset.filter(tags=self.object).with_last_send_letter()


class CaseListFree(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Case
    template_name_suffix = '_list_free'
    permission_required = "cases.can_view_free"
    raise_exception = True  # Aware infinity loop after redirect to login page

    def get_queryset(self, *args, **kwargs):
        queryset = super(CaseListFree, self).get_queryset(*args, **kwargs)
        return queryset.free().with_last_send_letter()


class CaseEdit(LoginRequiredMixin, FormValidMessageMixin, UpdateView, PermissionGroupMixin):
    model = Case
    fields = ("name", "status", "tags")

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)
