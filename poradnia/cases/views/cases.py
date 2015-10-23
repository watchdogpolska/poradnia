from __future__ import absolute_import

from braces.views import LoginRequiredMixin, UserFormKwargsMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, UpdateView
from django_filters.views import FilterView

from events.forms import EventForm
from letters.forms import AddLetterForm
from letters.helpers import AttachmentFormSet
from records.models import Record
from users.views import PermissionMixin

from ..filters import StaffCaseFilter, UserCaseFilter
from ..forms import CaseForm, CaseGroupPermissionForm
from ..models import Case


class CaseDetailView(LoginRequiredMixin, TemplateView):  # TODO: Use django.views.generic.DetailView
    template_name = 'cases/case_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        context = {}
        qs = (Case.objects.
              select_related('created_by').
              select_related('triggered').
              select_related('modified_by'))
        case = get_object_or_404(qs, pk=self.kwargs['pk'])
        case.view_perm_check(self.request.user)

        # Readed.update(user=request.user, case=case)

        context['object'] = case
        context['forms'] = {}
        context['forms']['letter'] = {'title': _('Letter'),
                                      'form': AddLetterForm(user=self.request.user, case=case),
                                      'formset': AttachmentFormSet(instance=None)}
        if self.request.user.is_staff:
            context['forms']['event'] = {'title': _('Event'),
                                         'form': EventForm(user=self.request.user, case=case)}

        qs = (Record.objects.filter(case=case).for_user(self.request.user).
              select_related('letter__created_by', 'letter', 'letter__modified_by').
              select_related('event__created_by', 'event', 'event__modified_by').
              select_related('event__alarm').
              prefetch_related('letter__attachment_set', 'letter__created_by__avatar_set'))
        context['record_list'] = qs.all()
        context['casegroup_form'] = CaseGroupPermissionForm(case=case, user=self.request.user)
        return context


class CaseListView(PermissionMixin, FilterView):
    model = Case
    paginate_by = 25

    @property
    def filterset_class(self):
        return StaffCaseFilter if self.request.user.is_staff else UserCaseFilter

    def get_queryset(self, *args, **kwargs):  # TODO: Mixins
        qs = super(CaseListView, self).get_queryset(*args, **kwargs)
        return qs.select_related('client').prefetch_related('tags')

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
