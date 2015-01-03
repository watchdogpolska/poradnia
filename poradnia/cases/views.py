from django.views.generic import DetailView, UpdateView, ListView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from braces.views import FormValidMessageMixin
from .models import Case
from .mixins import PermissionGroupMixin
from .tags.models import Tag


class CaseDetail(PermissionGroupMixin, DetailView):
    model = Case


class CaseList(PermissionGroupMixin, ListView):
    model = Case


class CaseObjectMixin(object):
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CaseList, self).get_context_data(**kwargs)
        # Add in the publisher
        context['object'] = self.object
        return context


class CaseListUser(CaseObjectMixin, CaseList):
    template_name_suffix = '_list_for_user'

    def get_queryset(self):
        self.object = get_object_or_404(get_user_model(), username=self.kwargs['username'])
        return self.model.objects.filter(client=self.object)


class CaseListTag(CaseObjectMixin, CaseList):
    template_name_suffix = '_list_for_tag'

    def get_queryset(self):
        self.object = get_object_or_404(Tag, pk=self.kwargs['tag_pk'])
        return self.model.objects.filter(tags=self.object)


class CaseListFree(CaseList):
    template_name_suffix = '_list_free'

    def get_queryset(self):
            return self.model.objects.free()


class CaseEdit(FormValidMessageMixin, UpdateView, PermissionGroupMixin):
    model = Case
    fields = ("name", "status", "tags")

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)
