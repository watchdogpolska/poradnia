
from django.views.generic import UpdateView, CreateView, DeleteView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from braces.views import (OrderableListMixin, SelectRelatedMixin, LoginRequiredMixin,
    FormValidMessageMixin, UserFormKwargsMixin)
from django_filters.views import FilterView
from users.utils import PermissionMixin
from utilities.views import DeleteMessageMixin, FormInitialMixin
from .filters import AdviceFilter
from .models import Advice
from .forms import AdviceForm


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


class AdviceDelete(PermissionMixin, DeleteMessageMixin, DeleteView):
    model = Advice
    success_url = reverse_lazy('advicer:list')
    success_message = _("{__unicode__} deleted!")
    hide_field = 'visible'


class AdviceDetail(PermissionMixin, DetailView):
    model = Advice
