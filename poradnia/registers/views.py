# from django.shortcuts import render
from django.views.generic import ListView, UpdateView, CreateView, DeleteView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from braces.views import SetHeadlineMixin
from braces.views import FormValidMessageMixin
from braces.views import OrderableListMixin
from braces.views import SelectRelatedMixin
from braces.views import UserFormKwargsMixin
from braces.views import LoginRequiredMixin
from .models import Advice
from .forms import AdviceForm


class PermissionMixin(LoginRequiredMixin, object):
    def get_queryset(self, *args, **kwargs):
        qs = super(PermissionMixin, self).get_queryset(*args, **kwargs)
        return qs.for_user(self.request.user)


class AdviceList(PermissionMixin, SelectRelatedMixin, OrderableListMixin, ListView):
    model = Advice
    orderable_columns = ("id", "advicer", "person_kind", "institution_kind")
    orderable_columns_default = "created_on"
    select_related = ["person_kind", "created_by", "advicer", "institution_kind"]

    def get_queryset(self, *args, **kwargs):
        qs = super(AdviceList, self).get_queryset(*args, **kwargs)
        return qs.visible()


class FormMixins(FormValidMessageMixin, SetHeadlineMixin, UserFormKwargsMixin):
    pass


class AdviceUpdate(PermissionMixin, FormMixins, UpdateView):
    model = Advice
    form_class = AdviceForm
    headline = _("Updating")

    def get_form_valid_message(self):
        return _("{0} updated!").format(self.object)


class AdviceCreate(FormMixins, LoginRequiredMixin, CreateView):
    model = Advice
    form_class = AdviceForm
    headline = _("Creating")

    def get_initial(self, *args, **kwargs):
        initial = super(AdviceCreate, self).get_initial(*args, **kwargs)
        initial.update(self.request.GET.dict())
        return initial

    def get_form_valid_message(self):
        return _("{0} created!").format(self.object)


class AdviceDelete(PermissionMixin, SetHeadlineMixin, DeleteView):
    model = Advice
    headline = _("Deleting")
    success_url = reverse_lazy('registers:list')

    def get_success_message(self):
        return _("{0} deleted!").format(self.object)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.visible = False
        self.object.save()
        messages.add_message(request, messages.SUCCESS, self.get_success_message())
        return HttpResponseRedirect(success_url)


class AdviceDetail(PermissionMixin, DetailView):
    model = Advice
