from __future__ import absolute_import

from braces.views import UserFormKwargsMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, UpdateView
from django_filters.views import FilterView

from cases.filters import StaffCaseFilter, UserCaseFilter
from cases.forms import CaseCloseForm, CaseForm, CaseGroupPermissionForm
from cases.models import Case
from events.forms import EventForm
from letters.forms import AddLetterForm
from letters.helpers import AttachmentFormSet
from records.models import Record
from users.views import PermissionMixin


class CaseDetailView(LoginRequiredMixin, TemplateView):  # TODO: Use django.views.generic.DetailView
    template_name = 'cases/case_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        context = {}
        qs = (Case.objects.
              select_related('created_by').
              select_related('modified_by').
              select_related('advice').
              select_related('deadline'))
        self.object = get_object_or_404(qs, pk=self.kwargs['pk'])
        self.object.view_perm_check(self.request.user)

        # Readed.update(user=request.user, case=case)

        context['object'] = self.object
        context['forms'] = {}
        context['forms']['letter'] = {'title': _('Letter'),
                                      'form': AddLetterForm(user=self.request.user,
                                                            case=self.object),
                                      'formset': AttachmentFormSet(instance=None)}
        if self.request.user.is_staff:
            context['forms']['event'] = {'title': _('Event'),
                                         'form': EventForm(user=self.request.user,
                                                           case=self.object)}
        qs = (Record.objects.filter(case=self.object).for_user(self.request.user).
              select_related('letter__created_by', 'letter', 'letter__modified_by').
              select_related('event__created_by', 'event', 'event__modified_by').
              select_related('event__alarm').
              prefetch_related('letter__attachment_set'))
        context['record_list'] = qs.all()
        context['casegroup_form'] = CaseGroupPermissionForm(case=self.object,
                                                            user=self.request.user)

        # Get next or prev objects
        try:
            context['next'] = self.object.get_next_for_user(self.request.user)
        except Case.DoesNotExist:
            context['next'] = None

        # Get next or prev objects
        try:
            context['previous'] = self.object.get_prev_for_user(self.request.user)
        except Case.DoesNotExist:
            context['previous'] = None

        return context


class CaseListView(PermissionMixin, FilterView):
    model = Case
    paginate_by = 25

    def get_filterset_class(self, *args, **kwargs):
        return StaffCaseFilter if self.request.user.is_staff else UserCaseFilter

    def get_filterset_kwargs(self, *args, **kwargs):
        kw = super(CaseListView, self).get_filterset_kwargs(*args, **kwargs)
        kw['user'] = self.request.user
        return kw

    def get_queryset(self, *args, **kwargs):  # TODO: Mixins
        qs = super(CaseListView, self).get_queryset(*args, **kwargs)
        qs = qs.select_related('client')
        if self.request.user.is_staff:
            qs = qs.with_involved_staff()
        return qs

    def get_context_data(self, **kwargs):
        context = super(CaseListView, self).get_context_data(**kwargs)
        context['statuses'] = Case.STATUS
        return context


class CaseUpdateView(UserFormKwargsMixin, UpdateView):
    form_class = CaseForm
    template_name = 'cases/case_form.html'
    model = Case

    def get_object(self):
        obj = super(CaseUpdateView, self).get_object()
        obj.perm_check(self.request.user, 'can_change_case')
        return obj

    def form_valid(self, form):
        obj = form.save()
        messages.success(self.request, _('Successful updated "%(object)s".') % {'object': obj})
        return redirect(obj)


class CaseCloseView(UserFormKwargsMixin, UpdateView):
    form_class = CaseCloseForm
    template_name = 'cases/case_close.html'
    model = Case

    def get_object(self):
        obj = super(CaseCloseView, self).get_object()
        obj.perm_check(self.request.user, 'can_close_case')
        return obj

    def form_valid(self, form):
        obj = form.save()
        messages.success(self.request, _('Successfully closed "%(object)s".') % {'object': obj})
        return redirect(obj)
