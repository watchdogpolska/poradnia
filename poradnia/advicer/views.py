from atom.ext.crispy_forms.views import FormSetMixin
from atom.views import ActionMessageMixin, ActionView, FormInitialMixin
from braces.views import (FormValidMessageMixin, LoginRequiredMixin,
                          SelectRelatedMixin, StaffuserRequiredMixin,
                          UserFormKwargsMixin)
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, UpdateView
from django_filters.views import FilterView

from poradnia.cases.models import Case
from poradnia.users.utils import PermissionMixin

from .filters import AdviceFilter
from .forms import AdviceForm, AttachmentForm
from .models import Advice, Attachment

try:
    from django.core.urlresolvers import reverse_lazy
except ImportError:
    from django.urls import reverse_lazy


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

    def get_initial(self, *args, **kwargs):
        initial = super(FormInitialMixin, self).get_initial(*args, **kwargs)
        if 'case' in self.request.GET.dict():
            case = get_object_or_404(
                Case.objects.for_user(self.request.user),
                pk=self.request.GET['case']
            )
            advicer = case.get_users_with_perms().\
                filter(is_staff=True).first()
            initial['advicer'] = advicer
        return initial


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
