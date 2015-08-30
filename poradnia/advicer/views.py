
from django.views.generic import UpdateView, CreateView, DeleteView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from braces.views import (SelectRelatedMixin, LoginRequiredMixin, FormValidMessageMixin,
    UserFormKwargsMixin, StaffuserRequiredMixin)
from django_filters.views import FilterView
from users.utils import PermissionMixin
from atom.views import DeleteMessageMixin, FormInitialMixin, FormSetMixin
from .filters import AdviceFilter
from .models import Advice, Attachment
from .forms import AdviceForm, AttachmentForm

ORDERING_TEXT = _("Ordering")


class AdviceList(StaffuserRequiredMixin, PermissionMixin, SelectRelatedMixin, FilterView):
    model = Advice
    filterset_class = AdviceFilter
    select_related = ["person_kind", "created_by", "advicer", "institution_kind"]
    paginate_by = 25
    raise_exception = True

    def get_queryset(self, *args, **kwargs):
        qs = super(AdviceList, self).get_queryset(*args, **kwargs)
        return qs.visible()


class AdviceUpdate(StaffuserRequiredMixin, FormSetMixin, PermissionMixin, FormValidMessageMixin,
                   UserFormKwargsMixin, UpdateView):
    model = Advice
    form_class = AdviceForm
    inline_model = Attachment
    inline_form_cls = AttachmentForm
    raise_exception = True

    def get_form_valid_message(self):
        return _("{0} updated!").format(self.object)

    def get_instance(self):
        return self.object


class AdviceCreate(StaffuserRequiredMixin, FormSetMixin, FormInitialMixin, UserFormKwargsMixin,
                   LoginRequiredMixin, CreateView):
    model = Advice
    form_class = AdviceForm
    inline_model = Attachment
    inline_form_cls = AttachmentForm
    raise_exception = True


class AdviceDelete(StaffuserRequiredMixin, PermissionMixin, DeleteMessageMixin, DeleteView):
    model = Advice
    success_url = reverse_lazy('advicer:list')
    success_message = _("{__unicode__} deleted!")
    hide_field = 'visible'
    raise_exception = True


class AdviceDetail(StaffuserRequiredMixin, PermissionMixin, DetailView):
    model = Advice
    raise_exception = True
