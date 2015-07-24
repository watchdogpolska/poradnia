from __future__ import absolute_import
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from letters.forms import AddLetterForm
from events.forms import EventForm
from letters.helpers import AttachmentFormSet
from pagination_custom.utils import paginator
from records.models import Record
from django.views.generic import UpdateView
from braces.views import UserFormKwargsMixin
from ..models import Case
from ..tags.models import Tag
from ..forms import CaseForm, CaseGroupPermissionForm


@login_required
def detail(request, pk):
    context = {}
    qs = (Case.objects.prefetch_related('tags').
          select_related('created_by').
          select_related('triggered').
          select_related('modified_by'))
    case = get_object_or_404(qs, pk=pk)
    case.view_perm_check(request.user)

    # Readed.update(user=request.user, case=case)

    context['object'] = case
    context['forms'] = {}
    context['forms']['letter'] = {'title': _('Letter'),
                                  'form': AddLetterForm(user=request.user, case=case),
                                  'formset': AttachmentFormSet(instance=None)}
    if request.user.is_staff:
        context['forms']['event'] = {'title': _('Event'),
                                     'form': EventForm(user=request.user, case=case)}

    qs = (Record.objects.filter(case=case).
        select_related('letter__created_by', 'letter', 'letter__modified_by').
        select_related('event__created_by', 'event', 'event__modified_by').
        select_related('event__alarm', ).

        prefetch_related('letter__attachment_set', 'letter__created_by__avatar_set'))

    if not request.user.is_staff:
        qs = qs.for_user(request.user)

    context['record_list'] = qs.all()
    context['casegroup_form'] = CaseGroupPermissionForm(case=case, user=request.user)

    return render(request, 'cases/case_detail.html', context)

SORT_MAP = {'deadline': 'deadline__time',
    'pk': 'pk',
    'client': 'client',
    'name': 'name',
    'created_on': 'created_on',
    'last_response': 'last_send',
    'last_action': 'last_action'}


@login_required
def list(request):
    context = {}
    context['statuses'] = Case.STATUS
    object_list = (Case.objects.
                   # with_read_time(request.user).
                   for_user(request.user).
                   select_related('client').
                   prefetch_related('tags'))

    # # # Filtering
    # TODO: Form or django-filter?
    # Show cases with TAG
    if 'tag' in request.GET:
        tag = get_object_or_404(Tag, pk=request.GET['tag'])
        object_list = object_list.filter(tags=tag)
        context['tag'] = tag

    # Show cases for CLIENT (USER)
    if 'user' in request.GET:
        user = get_user_model().objects.for_user(request.user)
        user = get_object_or_404(user, username=request.GET['user'])
        object_list = object_list.filter(client=user)
        context['user_filter'] = user

    # Show cases which has selected STATUS
    if 'status' in request.GET:
        object_list = object_list.filter(status=getattr(Case.STATUS, request.GET['status']))
        context['status'] = Case.STATUS[request.GET['status']]

    # Show cases which USER are involved
    if 'involved' in request.GET:
        user = get_user_model().objects.for_user(request.user)
        user = get_object_or_404(user, username=request.GET['user'])
        object_list = object_list.by_involved_in(user)
        context['involved'] = user

    # # # Ordering
    order_by = request.GET.get('order_by', 'deadline')  # get or default
    order_by = order_by if order_by in SORT_MAP else 'deadline'  # check exists
    order_key = SORT_MAP[order_by]  # get key
    ordering = 'asc' if request.GET.get('ordering') == 'asc' else 'desc'

    context['order_by'] = order_by
    context['ordering'] = ordering

    real_order_key = order_key if ordering == 'asc' else '-' + order_key

    object_list = object_list.order_by(real_order_key).all()
    context['object_list'] = paginator(request, object_list)

    return render(request, 'cases/case_list.html', context)


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
