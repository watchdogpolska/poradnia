# from django.shortcuts import render
from django.views.generic import ListView, UpdateView, CreateView, DeleteView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from braces.views import (OrderableListMixin, SelectRelatedMixin, LoginRequiredMixin,
    FormValidMessageMixin, UserFormKwargsMixin)
from ..filters import AdviceFilter
from ..models import Advice
from ..forms import AdviceForm
from .mixins import PermissionMixin, ListFilteredMixin


class AdviceList(PermissionMixin, ListFilteredMixin, SelectRelatedMixin,
        OrderableListMixin, ListView):
    model = Advice
    filter_set = AdviceFilter
    orderable_columns = ("id", "advicer", "person_kind", "institution_kind")
    orderable_columns_default = "created_on"
    select_related = ["person_kind", "created_by", "advicer", "institution_kind"]
    paginate_by = 25

    def get_queryset(self, *args, **kwargs):
        qs = super(AdviceList, self).get_queryset(*args, **kwargs)
        return qs.visible()


class AdviceUpdate(PermissionMixin, FormValidMessageMixin, UserFormKwargsMixin, UpdateView):
    model = Advice
    form_class = AdviceForm
    form_valid_message = _("{__unicode__} updated!")


class AdviceCreate(FormValidMessageMixin, UserFormKwargsMixin, LoginRequiredMixin, CreateView):
    model = Advice
    form_class = AdviceForm
    form_valid_message = _("{__unicode__} created!")


class AdviceDelete(PermissionMixin, DeleteView):
    model = Advice
    success_url = reverse_lazy('registers:list')
    success_message = _("{__unicode__} deleted!")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.visible = False
        self.object.save()
        messages.add_message(request, messages.SUCCESS, self.get_success_message())
        return HttpResponseRedirect(success_url)


class AdviceDetail(PermissionMixin, DetailView):
    model = Advice
