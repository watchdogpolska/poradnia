import django_filters
from atom.ext.crispy_forms.views import FormSetMixin
from atom.filters import CrispyFilterMixin
from braces.views import (PrefetchRelatedMixin, SelectRelatedMixin,
                          SetHeadlineMixin, UserFormKwargsMixin)
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, UpdateView
from django_filters.views import FilterView

from users.utils import PermissionMixin

from ..forms import AttachmentForm, LetterForm, NewCaseForm
from ..models import Attachment, Letter
from .fbv import REGISTRATION_TEXT


class NewCaseCreateView(SetHeadlineMixin, FormSetMixin, UserFormKwargsMixin, CreateView):
    model = Letter
    form_class = NewCaseForm
    headline = _('Create a new case')
    template_name = 'letters/form_new.html'
    inline_model = Attachment
    inline_form_cls = AttachmentForm

    def formset_valid(self, form, formset, *args, **kwargs):
        formset.save()
        messages.success(self.request,
                         _("Case about {object} created!").format(object=self.object.name))
        self.object.client.notify(actor=self.object.created_by,
                                  verb='registered',
                                  target=self.object.case,
                                  from_email=self.object.case.get_email())
        if self.request.user.is_anonymous():
            messages.success(self.request, _(REGISTRATION_TEXT) % {'user': self.object.created_by})
        return HttpResponseRedirect(self.object.case.get_absolute_url())


class LetterUpdateView(SetHeadlineMixin, FormSetMixin, UserFormKwargsMixin, UpdateView):
    model = Letter
    form_class = LetterForm
    headline = _('Edit')
    template_name = 'letters/form_edit.html'
    inline_model = Attachment
    inline_form_cls = AttachmentForm

    def get_context_data(self, **kwargs):
        context = super(LetterUpdateView, self).get_context_data(**kwargs)
        context['case'] = self.object.case
        return context

    def get_instance(self):
        return self.object

    def get_object(self):
        obj = super(LetterUpdateView, self).get_object()
        if obj.created_by_id == self.request.user.pk:
            obj.case.perm_check(self.request.user, 'can_change_own_record')
        else:
            obj.case.perm_check(self.request.user, 'can_change_all_record')
        return obj

    def get_formset_valid_message(self):
        return ("Letter %(object)s updated!") % {'object': self.object}

    def get_success_url(self):
        return self.object.case.get_absolute_url()

    def formset_valid(self, form, formset):
        resp = super(LetterUpdateView, self).formset_valid(form, formset)
        self.object.send_notification(actor=self.request.user, verb='updated')
        return resp


class StaffLetterFilter(CrispyFilterMixin, django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(StaffLetterFilter, self).__init__(*args, **kwargs)
        self.filters['status'].field.choices.insert(0, ('', u'---------'))

    class Meta:
        model = Letter
        fields = ['status', ]


class UserLetterFilter(CrispyFilterMixin, django_filters.FilterSet):
    class Meta:
        model = Letter
        fields = []


class LetterListView(PermissionMixin, SelectRelatedMixin, PrefetchRelatedMixin, FilterView):
    @property
    def filterset_class(self):
        return StaffLetterFilter if self.request.user.is_staff else UserLetterFilter

    model = Letter
    paginate_by = 5
    select_related = ['created_by', 'modified_by', 'case']
    prefetch_related = ['attachment_set', ]
