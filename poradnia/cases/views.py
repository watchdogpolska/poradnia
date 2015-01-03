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


class CaseListClient(CaseList):
    def get_queryset(self):
        if 'username' in self.kwargs:
            self.object = get_object_or_404(get_user_model(), username=self.kwargs['username'])
            return self.model.objects.filter(client=self.object)
        elif 'tag_pk' in self.kwargs:
            self.object = get_object_or_404(Tag, pk=self.kwargs['tag_pk'])
            return self.model.objects.filter(tags=self.object)
        else:
            raise NotImplementedError("Uknown kwargs pass")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CaseList, self).get_context_data(**kwargs)
        # Add in the publisher
        context['object'] = self.object
        return context


class CaseEdit(FormValidMessageMixin, UpdateView, PermissionGroupMixin):
    model = Case
    fields = ("name", "status", "tags")

    def get_form_valid_message(self):
        return u"{0} updated!".format(self.object)
