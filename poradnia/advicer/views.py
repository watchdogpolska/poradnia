
from atom.ext.crispy_forms.views import FormSetMixin
from atom.views import ActionMessageMixin, ActionView, FormInitialMixin
from braces.views import (FormValidMessageMixin, LoginRequiredMixin,
                          SelectRelatedMixin, StaffuserRequiredMixin,
                          UserFormKwargsMixin)
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, UpdateView
from django_filters.views import FilterView

from users.utils import PermissionMixin

from .filters import AdviceFilter
from .forms import AdviceForm, AttachmentForm
from .models import Advice, Attachment

ORDERING_TEXT = _("Ordering")


class VisibleMixin(object):
    def get_queryset(self, *args, **kwargs):
        qs = super(VisibleMixin, self).get_queryset(*args, **kwargs)
        return qs.visible()


class AdviceList(StaffuserRequiredMixin, PermissionMixin, SelectRelatedMixin, VisibleMixin,
                 FilterView):
    model = Advice
    filterset_class = AdviceFilter
    select_related = ["person_kind", "created_by", "advicer", "institution_kind",
                      "case__client"]
    paginate_by = 25
    raise_exception = True


class AdviceUpdate(StaffuserRequiredMixin, FormSetMixin, PermissionMixin, FormValidMessageMixin,
                   UserFormKwargsMixin, VisibleMixin, UpdateView):
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


class AdviceDelete(StaffuserRequiredMixin, PermissionMixin, ActionView, VisibleMixin,
                   ActionMessageMixin):
    model = Advice
    success_url = reverse_lazy('advicer:list')
    success_message = _("{subject} deleted!")
    template_name_suffix = '_confirm_delete'
    raise_exception = True

    def action(self):
        Advice.objects.filter(pk=self.object.pk).update(visible=False)


class AdviceDetail(StaffuserRequiredMixin, PermissionMixin, VisibleMixin, DetailView):
    model = Advice
    raise_exception = True
