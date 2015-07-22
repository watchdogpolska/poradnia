
from django.views.generic import UpdateView, CreateView, DeleteView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from braces.views import (OrderableListMixin, SelectRelatedMixin, LoginRequiredMixin,
    FormValidMessageMixin, UserFormKwargsMixin)
from django_filters.views import FilterView
from django.forms.models import inlineformset_factory
from django.contrib import messages
from users.utils import PermissionMixin
from utilities.views import DeleteMessageMixin, FormInitialMixin
from .filters import AdviceFilter
from .models import Advice, Attachment
from .forms import AdviceForm, AttachmentForm
from django.http import HttpResponseRedirect
from utilities.forms import BaseTableFormSet


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


class FormSetMixin(object):

    def get_instance(self):
        return None

    def get_formset(self):
        return inlineformset_factory(self.model, self.inline_model,
            form=self.inline_form_cls, formset=BaseTableFormSet)

    def get_context_data(self, **kwargs):
        context = super(FormSetMixin, self).get_context_data(**kwargs)
        context.update({'formset': self.get_formset()}(instance=self.get_instance()))
        return context

    def get_formset_valid_message(self):
        return _("{0} created!").format(self.object)

    def get_form(self, *args, **kwargs):
        form = super(FormSetMixin, self).get_form(*args, **kwargs)
        if hasattr(form, 'helper'):
            form.helper.form_tag = False
        return form

    def formset_valid(self, form, formset):
        formset.save()
        messages.success(self.request, self.get_formset_valid_message())
        return HttpResponseRedirect(self.object.get_absolute_url())

    def form_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        FormSet = self.get_formset()
        formset = FormSet(self.request.POST or None, self.request.FILES, instance=self.object)

        if formset.is_valid():
            self.object.save()
            return self.formset_valid(form, formset)
        else:
            return self.formset_invalid(form, formset)


class AdviceUpdate(FormSetMixin, PermissionMixin, FormValidMessageMixin, UserFormKwargsMixin,
        UpdateView):
    model = Advice
    form_class = AdviceForm
    inline_model = Attachment
    inline_form_cls = AttachmentForm

    def get_form_valid_message(self):
        return _("{0} updated!").format(self.object)

    def get_instance(self):
        return self.object


class AdviceCreate(FormSetMixin, FormInitialMixin, UserFormKwargsMixin, LoginRequiredMixin,
        CreateView):
    model = Advice
    form_class = AdviceForm
    inline_model = Attachment
    inline_form_cls = AttachmentForm


class AdviceDelete(PermissionMixin, DeleteMessageMixin, DeleteView):
    model = Advice
    success_url = reverse_lazy('advicer:list')
    success_message = _("{__unicode__} deleted!")
    hide_field = 'visible'


class AdviceDetail(PermissionMixin, DetailView):
    model = Advice
