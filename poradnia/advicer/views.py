from django.views.generic import UpdateView, CreateView, DeleteView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from braces.views import (OrderableListMixin, SelectRelatedMixin, LoginRequiredMixin,
    FormValidMessageMixin, UserFormKwargsMixin)
from utilities.views import FormInitialMixin
from users.utils import PermissionMixin
from .filters import AdviceFilter
from .models import Advice
from .forms import AdviceForm
from django_filters.views import FilterView


class AdviceList(PermissionMixin, SelectRelatedMixin,
        OrderableListMixin, FilterView):
    model = Advice
    filterset_class = AdviceFilter
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

    def get_form_valid_message(self):
        return _("{0} updated!").format(self.object)


class AdviceCreate(FormInitialMixin, FormValidMessageMixin, UserFormKwargsMixin, LoginRequiredMixin,
        CreateView):
    model = Advice
    form_class = AdviceForm

    def get_form_valid_message(self):
        return _("{0} created!").format(self.object)


class AdviceDelete(PermissionMixin, DeleteView):
    model = Advice
    success_url = reverse_lazy('advicer:list')
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
